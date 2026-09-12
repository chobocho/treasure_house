// -*- coding: utf-8 -*-
// DEFLATE 의 표들 — SPEC §10.3 (RFC 1951).
// 길이 부호 284 는 227..257 까지만, **길이 258 은 늘 285** 다.
#ifndef COMPRESSLIB_DEFLATE_TABLES_H
#define COMPRESSLIB_DEFLATE_TABLES_H

#include <array>

#include "common.h"

namespace compresslib {
namespace dfl {

constexpr size_t kMinMatch = 3;
constexpr size_t kMaxMatch = 258;
constexpr size_t kMaxDist = 32768;
constexpr int kEndOfBlock = 256;
constexpr size_t kLitlenSymbols = 286;
constexpr size_t kDistSymbols = 30;
constexpr size_t kClSymbols = 19;
constexpr int kClMaxLength = 7;
constexpr int kClRepeat = 16;
constexpr int kClZeroShort = 17;
constexpr int kClZeroLong = 18;

constexpr std::array<int, 29> kLengthExtra = {
    0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2,
    2, 3, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5, 0};
constexpr std::array<int, 29> kLengthBase = {
    3,  4,  5,  6,  7,  8,  9,  10, 11,  13,  15,  17,  19, 23,
    27, 31, 35, 43, 51, 59, 67, 83, 99, 115, 131, 163, 195, 227, 258};
constexpr std::array<int, 30> kDistExtra = {
    0, 0, 0, 0, 1, 1, 2, 2,  3,  3,  4,  4,  5,  5,  6,
    6, 7, 7, 8, 8, 9, 9, 10, 10, 11, 11, 12, 12, 13, 13};
constexpr std::array<int, 30> kDistBase = {
    1,    2,    3,    4,    5,    7,    9,    13,    17,    25,
    33,   49,   65,   97,   129,  193,  257,  385,   513,   769,
    1025, 1537, 2049, 3073, 4097, 6145, 8193, 12289, 16385, 24577};

// 자주 0 이 되는 것을 뒤로 몰아 HCLEN 으로 꼬리를 자를 수 있게 한 순서.
constexpr std::array<int, 19> kClOrder = {16, 17, 18, 0,  8,  7, 9,
                                          6,  10, 5,  11, 4,  12, 3,
                                          13, 2,  14, 1,  15};

inline const std::array<int, kMaxMatch + 1>& length_code_table() {
  static const std::array<int, kMaxMatch + 1> t = [] {
    std::array<int, kMaxMatch + 1> table{};
    for (size_t code = 0; code < kLengthBase.size(); ++code) {
      int base = kLengthBase[code];
      int top = base + (1 << kLengthExtra[code]) - 1;
      if (base == i32(kMaxMatch)) top = i32(kMaxMatch);
      for (int ln = base; ln <= top && ln <= i32(kMaxMatch); ++ln)
        table[sz(ln)] = 257 + i32(code);
    }
    table[kMaxMatch] = 285;      // 284 가 아니라 285 로 못 박는다
    return table;
  }();
  return t;
}

inline int length_code(size_t ln) { return length_code_table()[ln]; }

inline int dist_code(size_t dist) {
  for (int code = i32(kDistSymbols) - 1; code >= 0; --code)
    if (dist >= sz(kDistBase[sz(code)]))
      return code;
  fail("거리가 1보다 작다");
}

inline const std::vector<int>& fixed_litlen() {
  static const std::vector<int> v = [] {
    std::vector<int> l(288, 8);
    for (int s = 144; s < 256; ++s) l[sz(s)] = 9;
    for (int s = 256; s < 280; ++s) l[sz(s)] = 7;
    return l;
  }();
  return v;
}

inline const std::vector<int>& fixed_dist() {
  static const std::vector<int> v(32, 5);
  return v;
}

}  // namespace dfl
}  // namespace compresslib

#endif
