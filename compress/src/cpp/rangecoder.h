// -*- coding: utf-8 -*-
// 이진 레인지 코더 — SPEC §8. LZMA 의 것 그대로.
//
// C++ 에서 조심할 곳은 정수 승격이다. (range >> 11) * prob 은 uint32 와
// uint16 의 곱이라 int 로 승격돼 넘칠 수 있다 — prob 을 uint32 로 올려
// 둔다. low 는 2^33 까지 가므로 uint64 여야 한다.
#ifndef COMPRESSLIB_RANGECODER_H
#define COMPRESSLIB_RANGECODER_H

#include "common.h"
#include "varint.h"

namespace compresslib {
namespace rangecoder {

constexpr int kProbBits = 11;
constexpr uint32_t kProbTotal = 1u << kProbBits;
constexpr uint16_t kProbInit = u16(kProbTotal / 2);
constexpr int kMoveBits = 5;
constexpr uint32_t kTop = 1u << 24;

class Encoder {
 public:
  void encode_bit(std::vector<uint16_t>& probs, size_t i, int bit) {
    uint32_t bound = (range_ >> kProbBits) * u32(probs[i]);
    if (bit == 0) {
      range_ = bound;
      probs[i] =
          u16(probs[i] + ((kProbTotal - probs[i]) >> kMoveBits));
    } else {
      low_ += bound;
      range_ -= bound;
      probs[i] = u16(probs[i] - (probs[i] >> kMoveBits));
    }
    while (range_ < kTop) {
      range_ <<= 8;
      shift_low();
    }
  }
  void flush() {
    for (int i = 0; i < 5; ++i) shift_low();
  }
  const Bytes& bytes() const { return out_; }

 private:
  void shift_low() {
    if ((low_ >> 32) != 0 || low_ < 0xFF000000ull) {
      uint8_t carry = u8(low_ >> 32);
      uint8_t temp = cache_;
      do {
        out_.push_back(u8(temp + carry));
        temp = 0xFF;
        --cache_size_;
      } while (cache_size_ != 0);
      cache_ = u8((low_ >> 24) & 0xFF);
    }
    ++cache_size_;
    low_ = (low_ << 8) & 0xFFFFFFFFull;
  }

  uint64_t low_ = 0;
  uint32_t range_ = 0xFFFFFFFFu;
  uint8_t cache_ = 0;
  uint64_t cache_size_ = 1;
  Bytes out_;
};

class Decoder {
 public:
  Decoder(const Bytes& src, size_t pos) : src_(src), pos_(pos) {
    if (pos_ >= src_.size()) fail("레인지 코더 스트림이 비었다");
    if (src_[pos_] != 0) fail("첫 바이트가 0 이 아니다");
    ++pos_;
    for (int i = 0; i < 4; ++i) code_ = (code_ << 8) | next_byte();
  }
  int decode_bit(std::vector<uint16_t>& probs, size_t i) {
    uint32_t bound = (range_ >> kProbBits) * u32(probs[i]);
    int bit;
    if (code_ < bound) {
      range_ = bound;
      probs[i] =
          u16(probs[i] + ((kProbTotal - probs[i]) >> kMoveBits));
      bit = 0;
    } else {
      code_ -= bound;
      range_ -= bound;
      probs[i] = u16(probs[i] - (probs[i] >> kMoveBits));
      bit = 1;
    }
    while (range_ < kTop) {
      range_ <<= 8;
      code_ = (code_ << 8) | next_byte();
    }
    return bit;
  }

 private:
  uint32_t next_byte() {
    // 잘 만들어진 스트림도 마지막 판정에서 한 바이트쯤 더 읽는다.
    if (pos_ < src_.size()) return src_[pos_++];
    ++pos_;
    if (pos_ > src_.size() + 5) fail("스트림 끝을 너무 많이 넘었다");
    return 0;
  }
  const Bytes& src_;
  size_t pos_;
  uint32_t range_ = 0xFFFFFFFFu;
  uint32_t code_ = 0;
};

// 0차 적응 바이트 모델. 문맥은 1 에서 시작해 여덟 번 만에 256..511 이
// 되므로 실제로 쓰이는 자리는 1..255 뿐 — 배열이 257 이 아니라 256
// 이다.
struct ByteModel {
  std::vector<uint16_t> probs = std::vector<uint16_t>(256, kProbInit);

  void encode(Encoder& enc, uint8_t b) {
    int ctx = 1;
    for (int i = 7; i >= 0; --i) {
      int bit = (b >> i) & 1;
      enc.encode_bit(probs, sz(ctx), bit);
      ctx = (ctx << 1) | bit;
    }
  }
  uint8_t decode(Decoder& dec) {
    int ctx = 1;
    for (int i = 0; i < 8; ++i)
      ctx = (ctx << 1) | dec.decode_bit(probs, sz(ctx));
    return u8(ctx - 256);
  }
};

inline Bytes encode(const Bytes& src) {
  if (src.empty()) return varint::put(0);
  Encoder enc;
  ByteModel m;
  for (uint8_t b : src) m.encode(enc, b);
  enc.flush();
  Bytes out = varint::put(src.size());
  out.insert(out.end(), enc.bytes().begin(), enc.bytes().end());
  return out;
}

inline Bytes decode(const Bytes& src) {
  size_t pos = 0;
  size_t n = varint::get_length(src, pos);
  if (n == 0) {
    if (pos != src.size()) fail("빈 입력인데 뒤에 바이트가 있다");
    return Bytes();
  }
  Decoder dec(src, pos);
  ByteModel m;
  Bytes out;
  out.reserve(n);
  for (size_t i = 0; i < n; ++i) out.push_back(m.decode(dec));
  return out;
}

}  // namespace rangecoder
}  // namespace compresslib

#endif
