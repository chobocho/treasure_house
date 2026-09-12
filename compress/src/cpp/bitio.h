// -*- coding: utf-8 -*-
// 비트 writer/reader — SPEC §1.
//
// 두 가지 비트 순서를 다 쓴다. 우리 형식은 전부 MSB 먼저이고 DEFLATE 만
// LSB 먼저다. 가장 자주 갈라지는 자리는 flush 의 채움이다 — **채움은
// 0** 이고, 쌓인 비트가 없으면 바이트를 내보내지 않는다.
#ifndef COMPRESSLIB_BITIO_H
#define COMPRESSLIB_BITIO_H

#include "common.h"
#include "varint.h"

namespace compresslib {
namespace bitio {

class MsbWriter {
 public:
  void write_bit(int bit) {
    buf_ = u8(buf_ | ((bit & 1) << (7 - n_)));
    if (++n_ == 8) {
      out_.push_back(buf_);
      buf_ = 0;
      n_ = 0;
    }
  }
  void write_bits(uint64_t v, int count) {
    for (int i = count - 1; i >= 0; --i) write_bit(i32((v >> i) & 1));
  }
  // MSB 스트림에서는 값도 부호도 같은 순서다. 이름만 따로 둔 것은
  // LsbWriter 와 부르는 쪽 코드를 똑같이 만들기 위해서다.
  void write_code(uint64_t code, int count) { write_bits(code, count); }
  size_t bit_pos() const { return out_.size() * 8 + sz(n_); }
  void flush() {
    if (n_) {
      out_.push_back(buf_);
      buf_ = 0;
      n_ = 0;
    }
  }
  const Bytes& bytes() const { return out_; }

 private:
  Bytes out_;
  uint8_t buf_ = 0;
  int n_ = 0;
};

class MsbReader {
 public:
  MsbReader(const Bytes& src, size_t pos = 0) : src_(src), pos_(pos) {}
  int read_bit() {
    if (n_ == 0) {
      if (pos_ >= src_.size()) fail("비트 스트림이 바닥났다");
      buf_ = src_[pos_++];
      n_ = 8;
    }
    --n_;
    return (buf_ >> n_) & 1;
  }
  uint64_t read_bits(int count) {
    uint64_t v = 0;
    for (int i = 0; i < count; ++i) v = (v << 1) | u64(read_bit());
    return v;
  }
  void align() { n_ = 0; }
  size_t pos() const { return pos_; }
  void set_pos(size_t p) { pos_ = p; }
  size_t size() const { return src_.size(); }
  uint8_t at(size_t i) const { return src_[i]; }

 private:
  const Bytes& src_;
  size_t pos_;
  uint8_t buf_ = 0;
  int n_ = 0;
};

class LsbWriter {
 public:
  void write_bit(int bit) {
    buf_ = u8(buf_ | ((bit & 1) << n_));
    if (++n_ == 8) {
      out_.push_back(buf_);
      buf_ = 0;
      n_ = 0;
    }
  }
  void write_bits(uint64_t v, int count) {
    for (int i = 0; i < count; ++i) write_bit(i32((v >> i) & 1));
  }
  // 허프만 부호만 같은 LSB 스트림에 높은 비트부터 넣는다 (RFC 1951).
  void write_code(uint64_t code, int count) {
    for (int i = count - 1; i >= 0; --i)
      write_bit(i32((code >> i) & 1));
  }
  size_t bit_pos() const { return out_.size() * 8 + sz(n_); }
  void flush() {
    if (n_) {
      out_.push_back(buf_);
      buf_ = 0;
      n_ = 0;
    }
  }
  void align() { flush(); }
  const Bytes& bytes() const { return out_; }

 private:
  Bytes out_;
  uint8_t buf_ = 0;
  int n_ = 0;
};

class LsbReader {
 public:
  LsbReader(const Bytes& src, size_t pos = 0) : src_(src), pos_(pos) {}
  int read_bit() {
    if (n_ == 0) {
      if (pos_ >= src_.size()) fail("비트 스트림이 바닥났다");
      buf_ = src_[pos_++];
      n_ = 8;
    }
    int bit = buf_ & 1;
    buf_ = u8(buf_ >> 1);
    --n_;
    return bit;
  }
  uint64_t read_bits(int count) {
    uint64_t v = 0;
    for (int i = 0; i < count; ++i)
      v |= u64(read_bit()) << i;
    return v;
  }
  void align() { n_ = 0; }
  size_t pos() const { return pos_; }
  void set_pos(size_t p) { pos_ = p; }
  size_t size() const { return src_.size(); }
  uint8_t at(size_t i) const { return src_[i]; }

 private:
  const Bytes& src_;
  size_t pos_;
  uint8_t buf_ = 0;
  int n_ = 0;
};

// 골든 코덱 (SPEC §1.4). 앞의 0비트 셋이 요점 — 모든 바이트를 바이트
// 경계 밖으로 밀어내므로, 몰래 memcpy 하는 구현은 다른 파일을 낸다.
constexpr int kPadBits = 3;

inline Bytes encode(const Bytes& src) {
  MsbWriter w;
  w.write_bits(0, kPadBits);
  for (uint8_t b : src) w.write_bits(b, 8);
  w.flush();
  Bytes out = varint::put(src.size());
  out.insert(out.end(), w.bytes().begin(), w.bytes().end());
  return out;
}

inline Bytes decode(const Bytes& src) {
  size_t pos = 0;
  size_t n = varint::get_length(src, pos);
  MsbReader r(src, pos);
  r.read_bits(kPadBits);
  Bytes out;
  out.reserve(n);
  for (size_t i = 0; i < n; ++i)
    out.push_back(u8(r.read_bits(8)));
  return out;
}

}  // namespace bitio
}  // namespace compresslib

#endif
