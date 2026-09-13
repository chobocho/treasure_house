// -*- coding: utf-8 -*-
// 런 길이 부호 — SPEC §3.
//
// 정한 값 셋이 출력 바이트를 바꾼다: 문턱 3, 런 상한 128, 리터럴 상한
// 128. 리터럴 묶음을 min(j + r, i + 128) 로 자르는 것이 특히 중요하다 —
// 안 자르면 129바이트 묶음이 나오는데, 제어 바이트에 안 들어가는 길이라
// 아무도 못 푼다.
#ifndef COMPRESSLIB_RLE_H
#define COMPRESSLIB_RLE_H

#include <algorithm>

#include "common.h"
#include "varint.h"

namespace compresslib {
namespace rle {

constexpr size_t kRunMin = 3;
constexpr size_t kRunMax = 128;
constexpr size_t kLitMax = 128;
constexpr uint8_t kReserved = 128;

inline size_t run_at(const Bytes& src, size_t i, size_t cap = kRunMax) {
  uint8_t b = src[i];
  size_t j = i + 1;
  size_t end = std::min(src.size(), i + cap);
  while (j < end && src[j] == b) ++j;
  return j - i;
}

inline void pack(const Bytes& src, Bytes& out) {
  size_t i = 0, n = src.size();
  while (i < n) {
    size_t run = run_at(src, i);
    if (run >= kRunMin) {
      out.push_back(u8(257 - run));
      out.push_back(src[i]);
      i += run;
      continue;
    }
    size_t j = i;
    while (j < n && (j - i) < kLitMax) {
      size_t r = run_at(src, j);
      if (r >= kRunMin) break;
      j = std::min(j + r, i + kLitMax);
    }
    out.push_back(u8(j - i - 1));
    out.insert(out.end(), src.begin() + ix(i),
               src.begin() + ix(j));
    i = j;
  }
}

inline Bytes unpack(const Bytes& src, size_t& pos, size_t want) {
  Bytes out;
  out.reserve(want);
  size_t n = src.size();
  while (out.size() < want) {
    if (pos >= n) fail("PackBits 가 잘렸다");
    uint8_t c = src[pos++];
    if (c == kReserved) fail("제어 128 은 쓰지 않는다");
    if (c < kReserved) {
      size_t k = sz(c) + 1;
      if (pos + k > n) fail("리터럴 묶음이 잘렸다");
      out.insert(out.end(), src.begin() + ix(pos),
                 src.begin() + ix(pos + k));
      pos += k;
    } else {
      size_t k = 257 - sz(c);
      if (pos >= n) fail("런 묶음이 잘렸다");
      out.insert(out.end(), k, src[pos]);
      ++pos;
    }
  }
  if (out.size() != want) fail("푼 길이가 헤더와 다르다");
  return out;
}

inline Bytes encode(const Bytes& src) {
  Bytes out = varint::put(src.size());
  pack(src, out);
  return out;
}

inline Bytes decode(const Bytes& src) {
  size_t pos = 0;
  size_t n = varint::get_length(src, pos);
  Bytes out = unpack(src, pos, n);
  if (pos != src.size()) fail("뒤에 남은 바이트가 있다");
  return out;
}

// 0런 부호 (SPEC §3.2) — bzip2 의 RUNA/RUNB. bzip2dec(§15)이 쓴다.
constexpr int kRunA = 0;
constexpr int kRunB = 1;

inline std::vector<int> zero_run_encode(const std::vector<int>& syms) {
  std::vector<int> out;
  size_t i = 0, n = syms.size();
  while (i < n) {
    if (syms[i] != 0) {
      out.push_back(syms[i] + 1);
      ++i;
      continue;
    }
    size_t j = i;
    while (j < n && syms[j] == 0) ++j;
    uint64_t length = u64(j - i) + 1;
    while (length > 1) {
      out.push_back((length & 1) ? kRunB : kRunA);
      length >>= 1;
    }
    i = j;
  }
  return out;
}

inline std::vector<int> zero_run_decode(const std::vector<int>& syms) {
  std::vector<int> out;
  size_t i = 0, n = syms.size();
  while (i < n) {
    if (syms[i] > 1) {
      out.push_back(syms[i] - 1);
      ++i;
      continue;
    }
    uint64_t run = 0, weight = 1;
    while (i < n && syms[i] <= 1) {
      run += u64(syms[i] + 1) * weight;
      weight <<= 1;
      ++i;
    }
    out.insert(out.end(), run, 0);
  }
  return out;
}

}  // namespace rle
}  // namespace compresslib

#endif
