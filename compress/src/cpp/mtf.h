// -*- coding: utf-8 -*-
// move-to-front — SPEC §4.
//
// 앞으로 **옮기는** 것이지 바꿔치는 것이 아니다. 바꿔치기도
// 자기들끼리는 왕복이 되므로, 골든 벡터가 없으면 갈라진 줄도 모른다.
// 표를 그냥 배열로 둔다 — 최악 O(n·256). 덱에 실린 코드가 곧 숫자를 낸
// 코드다.
#ifndef COMPRESSLIB_MTF_H
#define COMPRESSLIB_MTF_H

#include "common.h"
#include "varint.h"

namespace compresslib {
namespace mtf {

constexpr int kAlphabet = 256;

inline Bytes transform(const Bytes& src) {
  uint8_t table[kAlphabet];
  for (int i = 0; i < kAlphabet; ++i) table[i] = u8(i);
  Bytes out;
  out.reserve(src.size());
  for (uint8_t b : src) {
    int i = 0;
    while (table[i] != b) ++i;
    out.push_back(u8(i));
    for (int k = i; k > 0; --k) table[k] = table[k - 1];
    table[0] = b;
  }
  return out;
}

inline Bytes inverse(const Bytes& src) {
  uint8_t table[kAlphabet];
  for (int i = 0; i < kAlphabet; ++i) table[i] = u8(i);
  Bytes out;
  out.reserve(src.size());
  for (uint8_t idx : src) {
    uint8_t b = table[idx];
    out.push_back(b);
    for (int k = idx; k > 0; --k) table[k] = table[k - 1];
    table[0] = b;
  }
  return out;
}

inline Bytes encode(const Bytes& src) {
  Bytes out = varint::put(src.size());
  Bytes body = transform(src);
  out.insert(out.end(), body.begin(), body.end());
  return out;
}

inline Bytes decode(const Bytes& src) {
  size_t pos = 0;
  size_t n = varint::get_length(src, pos);
  if (src.size() - pos != n) fail("몸통 길이가 헤더와 다르다");
  Bytes body(src.begin() + ix(pos), src.end());
  return inverse(body);
}

}  // namespace mtf
}  // namespace compresslib

#endif
