// -*- coding: utf-8 -*-
// 버로우즈–휠러 변환 — SPEC §9.
//
// 배가 늘리기 정렬. 키를 rank[i]*(m+1) + rank[i+k] 로 눌러 담는데, **첫
// 회의 rank 를 바이트 값 그대로 쓰면 안 된다** — 곱수 m+1 이 255 보다
// 작아져 자리가 겹친다. 0..(서로 다른 값 수-1) 로 먼저 압축한다. 같은
// 회전이 여럿이면 순서는 시작 위치 오름차순 — 안정 정렬이 필요하다.
#ifndef COMPRESSLIB_BWT_H
#define COMPRESSLIB_BWT_H

#include <algorithm>
#include <numeric>

#include "common.h"
#include "varint.h"

namespace compresslib {
namespace bwt {

constexpr size_t kBlock = size_t{1} << 16;
constexpr int kAlphabet = 256;

inline void transform_block(const Bytes& block, Bytes& out_l,
                            uint32_t& out_primary) {
  size_t m = block.size();
  out_l.clear();
  out_primary = 0;
  if (m == 0) return;

  int order[kAlphabet];
  for (int i = 0; i < kAlphabet; ++i) order[i] = -1;
  for (uint8_t c : block) order[c] = 1;
  int next = 0;
  for (int i = 0; i < kAlphabet; ++i)
    if (order[i] > 0) order[i] = next++;

  std::vector<uint64_t> rank(m), keys(m), new_rank(m);
  for (size_t i = 0; i < m; ++i)
    rank[i] = u64(order[block[i]]);
  std::vector<uint32_t> sa(m);
  std::iota(sa.begin(), sa.end(), 0u);

  uint64_t mul = u64(m) + 1;
  for (size_t k = 1;; k *= 2) {
    for (size_t i = 0; i < m; ++i)
      keys[i] = rank[i] * mul + rank[(i + k) % m];
    std::stable_sort(sa.begin(), sa.end(),
                     [&keys](uint32_t a, uint32_t b) {
                       return keys[a] < keys[b];
                     });
    uint64_t r = 0;
    new_rank[sa[0]] = 0;
    for (size_t j = 1; j < m; ++j) {
      if (keys[sa[j]] != keys[sa[j - 1]]) ++r;
      new_rank[sa[j]] = r;
    }
    rank = new_rank;
    if (r == m - 1 || k >= m) break;
  }
  out_l.reserve(m);
  for (size_t j = 0; j < m; ++j) {
    size_t i = sa[j];
    out_l.push_back(block[(i + m - 1) % m]);
    if (i == 0) out_primary = u32(j);
  }
}

inline Bytes inverse_block(const Bytes& l, uint32_t primary) {
  size_t m = l.size();
  if (m == 0) return Bytes();
  if (primary >= m) fail("primary 가 범위 밖이다");
  std::vector<uint32_t> count(kAlphabet, 0), first(kAlphabet, 0),
      occ(kAlphabet, 0);
  for (uint8_t c : l) count[c] += 1;
  uint32_t total = 0;
  for (int c = 0; c < kAlphabet; ++c) {
    first[sz(c)] = total;
    total += count[sz(c)];
  }
  std::vector<uint32_t> nxt(m);
  for (size_t i = 0; i < m; ++i) {
    uint8_t c = l[i];
    nxt[first[c] + occ[c]] = u32(i);
    occ[c] += 1;
  }
  Bytes out;
  out.reserve(m);
  size_t i = primary;
  for (size_t step = 0; step < m; ++step) {
    i = nxt[i];
    out.push_back(l[i]);
  }
  return out;
}

inline Bytes encode(const Bytes& src) {
  Bytes out = varint::put(src.size());
  Bytes l;
  uint32_t primary = 0;
  for (size_t off = 0; off < src.size(); off += kBlock) {
    size_t m = std::min(kBlock, src.size() - off);
    Bytes block(src.begin() + ix(off),
                src.begin() + ix(off + m));
    transform_block(block, l, primary);
    for (int b = 0; b < 4; ++b)
      out.push_back(u8((primary >> (8 * b)) & 0xFF));
    out.insert(out.end(), l.begin(), l.end());
  }
  return out;
}

inline Bytes decode(const Bytes& src) {
  size_t pos = 0;
  size_t n = varint::get_length(src, pos);
  Bytes out;
  out.reserve(n);
  size_t left = n;
  while (left > 0) {
    size_t m = std::min(kBlock, left);
    if (pos + 4 + m > src.size()) fail("블록이 잘렸다");
    uint32_t primary = 0;
    for (int b = 0; b < 4; ++b)
      primary |= u32(src[pos + sz(b)]) << (8 * b);
    pos += 4;
    Bytes l(src.begin() + ix(pos),
            src.begin() + ix(pos + m));
    Bytes part = inverse_block(l, primary);
    out.insert(out.end(), part.begin(), part.end());
    pos += m;
    left -= m;
  }
  if (pos != src.size()) fail("뒤에 남은 바이트가 있다");
  return out;
}

}  // namespace bwt
}  // namespace compresslib

#endif
