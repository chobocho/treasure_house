// -*- coding: utf-8 -*-
// ANS — 비대칭 수 체계 — SPEC §13.
//
// rANS 는 **스택** 이다. 부호기가 입력을 뒤에서부터 밀어 넣고 복호기가
// 앞에서부터 꺼낸다. 상태 x 는 (x / f) * TOTAL 에서 2^31 에 닿으므로
// 부호 있는 32비트로는 모자란다 — uint32_t 여야 한다.
#ifndef COMPRESSLIB_ANS_H
#define COMPRESSLIB_ANS_H

#include <algorithm>

#include "common.h"
#include "varint.h"

namespace compresslib {
namespace ans {

constexpr int kTotalBits = 12;
constexpr uint32_t kTotal = 1u << kTotalBits;
constexpr uint32_t kL = 1u << 23;
constexpr int kAlphabet = 256;
// tANS 의 퍼뜨리기 걸음 (zstd 의 값). 홀수라서 2의 거듭제곱 칸을
// 빠짐없이 한 번씩 돈다.
constexpr uint32_t kSpreadStep = (kTotal >> 1) + (kTotal >> 3) + 3;

// 빈도를 합이 정확히 kTotal 이 되게 고친다 (SPEC §13.3).
// 남으면 가장 큰 기호에 한꺼번에, 모자라면 가장 큰 데서 되풀이해 뺀다.
// 동점이면 번호가 작은 쪽.
inline std::vector<uint32_t> normalise(
    const std::vector<uint64_t>& counts) {
  uint64_t total = 0;
  for (uint64_t c : counts) total += c;
  std::vector<uint32_t> f(kAlphabet, 0);
  if (total == 0) return f;
  for (int s = 0; s < kAlphabet; ++s) {
    if (counts[sz(s)]) {
      uint64_t v = counts[sz(s)] * kTotal / total;
      f[sz(s)] = u32(std::max<uint64_t>(1, v));
    }
  }
  int64_t sum = 0;
  for (uint32_t v : f) sum += v;
  int64_t d = i32(kTotal) - sum;
  while (d != 0) {
    int best = 0;
    for (int s = 1; s < kAlphabet; ++s) {
      if (f[sz(s)] > f[sz(best)]) best = s;
    }
    if (d > 0) {
      f[sz(best)] += u32(d);
      d = 0;
    } else {
      int64_t take = std::min<int64_t>(-d, i32(f[sz(best)]) - 1);
      if (take == 0) fail("빈도를 TOTAL 에 못 맞춘다");
      f[sz(best)] -= u32(take);
      d += take;
    }
  }
  return f;
}

inline std::vector<uint32_t> cumulative(
    const std::vector<uint32_t>& f) {
  std::vector<uint32_t> cum(kAlphabet, 0);
  uint32_t total = 0;
  for (int s = 0; s < kAlphabet; ++s) {
    cum[sz(s)] = total;
    total += f[sz(s)];
  }
  return cum;
}

inline std::vector<uint8_t> slot_symbols(
    const std::vector<uint32_t>& f, const std::vector<uint32_t>& cum) {
  std::vector<uint8_t> slots(kTotal, 0);
  for (int s = 0; s < kAlphabet; ++s) {
    for (uint32_t i = cum[sz(s)]; i < cum[sz(s)] + f[sz(s)]; ++i) {
      slots[i] = u8(s);
    }
  }
  return slots;
}

// tANS 의 상태표 (SPEC §13.6). 골든에는 안 들어가고 12부가 쓴다.
inline std::vector<uint8_t> tans_table(const std::vector<uint32_t>& f) {
  std::vector<uint8_t> table(kTotal, 0);
  uint32_t pos = 0;
  for (int s = 0; s < kAlphabet; ++s) {
    for (uint32_t i = 0; i < f[sz(s)]; ++i) {
      table[pos] = u8(s);
      pos = (pos + kSpreadStep) & (kTotal - 1);
    }
  }
  return table;
}

inline Bytes encode(const Bytes& src) {
  if (src.empty()) return varint::put(0);
  std::vector<uint64_t> counts(kAlphabet, 0);
  for (uint8_t b : src) counts[b] += 1;
  std::vector<uint32_t> f = normalise(counts);
  std::vector<uint32_t> cum = cumulative(f);

  Bytes body;
  uint32_t x = kL;
  // 뒤에서부터 민다. rANS 는 스택이라 마지막에 넣은 것이 먼저 나온다.
  for (size_t i = src.size(); i > 0; --i) {
    uint32_t s = src[i - 1];
    uint32_t fs = f[s];
    uint32_t x_max = ((kL >> kTotalBits) << 8) * fs;
    while (x >= x_max) {
      body.push_back(u8(x & 0xFF));
      x >>= 8;
    }
    x = (x / fs) * kTotal + (x % fs) + cum[s];
  }
  for (int i = 0; i < 4; ++i) body.push_back(u8((x >> (8 * i)) & 0xFF));
  std::reverse(body.begin(), body.end());

  Bytes out = varint::put(src.size());
  for (int s = 0; s < kAlphabet; ++s) varint::put(out, f[sz(s)]);
  out.insert(out.end(), body.begin(), body.end());
  return out;
}

inline Bytes decode(const Bytes& src) {
  size_t pos = 0;
  size_t n = varint::get_length(src, pos);
  if (n == 0) {
    if (pos != src.size()) fail("빈 입력인데 뒤에 바이트가 있다");
    return Bytes();
  }
  std::vector<uint32_t> f(kAlphabet, 0);
  uint64_t sum = 0;
  for (int s = 0; s < kAlphabet; ++s) {
    uint64_t v = varint::get(src, pos);
    if (v > kTotal) fail("빈도가 TOTAL 을 넘는다");
    f[sz(s)] = u32(v);
    sum += v;
  }
  if (sum != kTotal) fail("빈도의 합이 TOTAL 이 아니다");
  std::vector<uint32_t> cum = cumulative(f);
  std::vector<uint8_t> slots = slot_symbols(f, cum);

  size_t at = pos;
  if (src.size() - at < 4) fail("rANS 스트림이 너무 짧다");
  uint32_t x = 0;
  for (int i = 0; i < 4; ++i) x = (x << 8) | src[at + sz(i)];
  at += 4;
  Bytes out;
  out.reserve(n);
  const uint32_t mask = kTotal - 1;
  for (size_t k = 0; k < n; ++k) {
    uint32_t slot = x & mask;
    uint8_t s = slots[slot];
    out.push_back(s);
    x = f[s] * (x >> kTotalBits) + slot - cum[s];
    while (x < kL) {
      if (at >= src.size()) fail("rANS 스트림이 모자란다");
      x = (x << 8) | src[at++];
    }
  }
  if (at != src.size()) fail("뒤에 남은 바이트가 있다");
  return out;
}

}  // namespace ans
}  // namespace compresslib

#endif
