// -*- coding: utf-8 -*-
// LZ78 계열 — SPEC §7.
//
// **복호기는 부호기보다 항목 하나 뒤처진다.** 그래서 폭을 늘리는 조건이
// 부호기는 next_free, 복호기는 next_free + 1 이다. 이 한 칸을 틀리면
// 사전 254번째 항목쯤부터 어긋난다 — 작은 시험은 전부 통과한다.
#ifndef COMPRESSLIB_LZW_H
#define COMPRESSLIB_LZW_H

#include <map>

#include "bitio.h"
#include "common.h"
#include "varint.h"

namespace compresslib {
namespace lzw {

constexpr int kClear = 256;
constexpr int kEof = 257;
constexpr int kFirstFree = 258;
constexpr int kMinWidth = 9;
constexpr int kMaxWidth = 12;
constexpr int kDictCap = 1 << kMaxWidth;

inline Bytes encode(const Bytes& src) {
  if (src.empty()) return varint::put(0);
  bitio::MsbWriter w;
  // (앞 부호, 다음 바이트) → 부호. 사전을 트라이로 두는 것과 같다.
  std::map<std::pair<int, uint8_t>, int> table;
  int next_free = kFirstFree;
  int width = kMinWidth;
  int cur = -1;
  for (uint8_t k : src) {
    if (cur < 0) {
      cur = k;
      continue;
    }
    auto it = table.find({cur, k});
    if (it != table.end()) {
      cur = it->second;
      continue;
    }
    w.write_bits(u64(cur), width);
    if (next_free == kDictCap) {
      w.write_bits(kClear, width);
      table.clear();
      next_free = kFirstFree;
      width = kMinWidth;
    } else {
      table[{cur, k}] = next_free++;
      // 폭 검사는 항목을 넣은 뒤에 — 이 부호가 아니라 다음 부호부터
      // 넓어진다.
      if (next_free == (1 << width) && width < kMaxWidth) ++width;
    }
    cur = k;
  }
  if (cur >= 0) w.write_bits(u64(cur), width);
  w.write_bits(kEof, width);
  w.flush();
  Bytes out = varint::put(src.size());
  out.insert(out.end(), w.bytes().begin(), w.bytes().end());
  return out;
}

inline Bytes decode(const Bytes& src) {
  size_t pos = 0;
  size_t n = varint::get_length(src, pos);
  if (n == 0) {
    if (pos != src.size()) fail("빈 입력인데 뒤에 바이트가 있다");
    return Bytes();
  }
  bitio::MsbReader r(src, pos);
  Bytes out;
  out.reserve(n);
  std::vector<Bytes> table(sz(kDictCap));
  int next_free = kFirstFree;
  int width = kMinWidth;
  bool has_prev = false;
  Bytes prev;
  for (;;) {
    int code = i32(r.read_bits(width));
    if (code == kEof) break;
    if (code == kClear) {
      next_free = kFirstFree;
      width = kMinWidth;
      has_prev = false;
      continue;
    }
    Bytes entry;
    if (!has_prev) {
      if (code >= kClear) fail("첫 부호가 리터럴이 아니다");
      entry.push_back(u8(code));
    } else if (code < 256) {
      entry.push_back(u8(code));
    } else if (code < next_free) {
      entry = table[sz(code)];
    } else if (code == next_free) {
      entry = prev;                       // KwKwK
      entry.push_back(prev[0]);
    } else {
      fail("아직 없는 부호");
    }
    out.insert(out.end(), entry.begin(), entry.end());
    if (out.size() > n) fail("푼 길이가 헤더를 넘었다");
    if (has_prev) {
      Bytes added = prev;
      added.push_back(entry[0]);
      table[sz(next_free)] = added;
      ++next_free;
      // 복호기는 한 칸 뒤처져 있다. + 1 이 그 보정이다.
      if (next_free + 1 == (1 << width) && width < kMaxWidth) ++width;
    }
    prev = entry;
    has_prev = true;
  }
  if (out.size() != n) fail("푼 길이가 헤더와 다르다");
  return out;
}

}  // namespace lzw
}  // namespace compresslib

#endif
