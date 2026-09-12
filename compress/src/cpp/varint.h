// -*- coding: utf-8 -*-
// LEB128 가변 길이 정수 — SPEC §2.1.
//
// 명세에서는 intcode 의 일부지만 파일을 갈랐다. 모든 코덱 헤더가 varint
// 로 시작하는데 intcode 는 비트 스트림을 쓰고 bitio 의 골든 코덱은 다시
// varint 를 쓴다 — 한 곳에 두면 서로를 먼저 필요로 한다. 다섯 언어 모두
// 같은 이유로 같게 갈라 뒀다.
#ifndef COMPRESSLIB_VARINT_H
#define COMPRESSLIB_VARINT_H

#include "common.h"

namespace compresslib {
namespace varint {

constexpr int kMaxBytes = 10;
// 길이 칸의 상한. 손상된 헤더가 불가능한 할당을 요구하지 못하게 막는다.
constexpr uint64_t kMaxLength = 0xFFFFFFFFull;

inline void put(Bytes& out, uint64_t value) {
  for (;;) {
    uint8_t b = u8(value & 0x7F);
    value >>= 7;
    if (value != 0) {
      out.push_back(u8(b | 0x80));
    } else {
      out.push_back(b);
      return;
    }
  }
}

inline Bytes put(uint64_t value) {
  Bytes out;
  put(out, value);
  return out;
}

// (값, 다음 위치). 10바이트를 넘거나 64비트를 넘으면 예외.
inline uint64_t get(const Bytes& src, size_t& pos) {
  uint64_t value = 0;
  int shift = 0;
  for (int i = 0; i < kMaxBytes; ++i) {
    if (pos >= src.size()) fail("varint 가 잘렸다");
    uint8_t b = src[pos++];
    // i == 9 일 때 7비트를 다 쓰면 64비트를 넘는다. 조용히 감기지 않게
    // 막는다.
    if (i == kMaxBytes - 1 && (b & 0x7F) > 1)
      fail("varint 가 64비트를 넘는다");
    value |= u64(b & 0x7F) << shift;
    if ((b & 0x80) == 0) return value;
    shift += 7;
  }
  fail("varint 가 10바이트를 넘는다");
}

inline size_t get_length(const Bytes& src, size_t& pos) {
  uint64_t v = get(src, pos);
  if (v > kMaxLength) fail("길이 칸이 너무 크다");
  return sz(v);
}

}  // namespace varint
}  // namespace compresslib

#endif
