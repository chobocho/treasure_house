// -*- coding: utf-8 -*-
// 정수 부호 — SPEC §2.
//
// varint 만 바이트 단위이고 감마·델타·라이스는 비트 스트림(MSB
// 먼저)에서 돈다. 단항은 **1 을 q개 쓰고 0 으로 닫는다** — 반대 약속도
// 문헌에 흔한데, 섞어 쓰면 작은 값은 그대로 왕복돼서 골든 벡터 전에는
// 안 보인다.
#ifndef COMPRESSLIB_INTCODE_H
#define COMPRESSLIB_INTCODE_H

#include "bitio.h"
#include "common.h"
#include "varint.h"

namespace compresslib {
namespace intcode {

// 단항 상한 (SPEC §2.5). 손상된 파일이 무한 루프가 되지 않게 하되,
// k=0 인 라이스(= 순수 단항)가 쓸모 있을 만큼은 크게.
constexpr uint64_t kMaxUnary = 4096;

inline uint64_t zigzag(int64_t n) {
  return (u64(n) << 1) ^ u64(n >> 63);
}

inline int64_t unzigzag(uint64_t u) {
  return static_cast<int64_t>((u >> 1) ^ (~(u & 1) + 1));
}

inline int bit_length(uint64_t v) {
  int n = 0;
  while (v) {
    ++n;
    v >>= 1;
  }
  return n;
}

inline void put_gamma(bitio::MsbWriter& w, uint64_t v) {
  if (v < 1) fail("gamma 는 1 이상만");
  int n = bit_length(v);
  w.write_bits(0, n - 1);
  w.write_bits(v, n);
}

inline uint64_t get_gamma(bitio::MsbReader& r) {
  int n = 1;
  while (r.read_bit() == 0) {
    if (++n > 64) fail("gamma 의 길이 부분이 64비트를 넘는다");
  }
  return (uint64_t{1} << (n - 1)) | r.read_bits(n - 1);
}

inline void put_delta(bitio::MsbWriter& w, uint64_t v) {
  if (v < 1) fail("delta 는 1 이상만");
  int n = bit_length(v);
  put_gamma(w, u64(n));
  w.write_bits(v, n - 1);
}

inline uint64_t get_delta(bitio::MsbReader& r) {
  uint64_t n = get_gamma(r);
  if (n > 64) fail("delta 의 길이 부분이 64비트를 넘는다");
  return (uint64_t{1} << (n - 1)) | r.read_bits(i32(n) - 1);
}

inline void put_rice(bitio::MsbWriter& w, uint64_t v, int k) {
  uint64_t q = v >> k;
  if (q > kMaxUnary) fail("rice 의 몫이 너무 크다 — k 를 잘못 골랐다");
  for (uint64_t i = 0; i < q; ++i) w.write_bit(1);
  w.write_bit(0);
  if (k) w.write_bits(v & ((uint64_t{1} << k) - 1), k);
}

inline uint64_t get_rice(bitio::MsbReader& r, int k) {
  uint64_t q = 0;
  while (r.read_bit() == 1) {
    if (++q > kMaxUnary) fail("rice 의 단항이 상한을 넘는다");
  }
  return (q << k) | (k ? r.read_bits(k) : 0);
}

// 골든 코덱 (SPEC §2.6) — 바이트마다 gamma(b+1).
inline Bytes encode(const Bytes& src) {
  bitio::MsbWriter w;
  for (uint8_t b : src) put_gamma(w, u64(b) + 1);
  w.flush();
  Bytes out = varint::put(src.size());
  out.insert(out.end(), w.bytes().begin(), w.bytes().end());
  return out;
}

inline Bytes decode(const Bytes& src) {
  size_t pos = 0;
  size_t n = varint::get_length(src, pos);
  bitio::MsbReader r(src, pos);
  Bytes out;
  out.reserve(n);
  for (size_t i = 0; i < n; ++i) {
    uint64_t v = get_gamma(r) - 1;
    if (v > 255) fail("바이트 범위를 벗어난 값");
    out.push_back(u8(v));
  }
  return out;
}

}  // namespace intcode
}  // namespace compresslib

#endif
