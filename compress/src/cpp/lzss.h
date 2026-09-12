// -*- coding: utf-8 -*-
// LZ77 계열 — SPEC §6.
//
// 사슬 배열을 **절대 위치로** 잡는다. zlib 은 창 크기 배열에 감아
// 넣어서 pos - 32768 자리를 pos 가 덮어쓰고, 그래서 실효 최대 거리가
// 32506 이다. 후보 교체 비교는 > 다. >= 로 쓰면 같은 길이에서 먼 쪽을
// 골라, 정상 복호되는 **다른** 파일이 나온다.
#ifndef COMPRESSLIB_LZSS_H
#define COMPRESSLIB_LZSS_H

#include <algorithm>

#include "common.h"
#include "varint.h"

namespace compresslib {
namespace lzss {

constexpr size_t kWindow = 32768;
constexpr size_t kMinMatch = 3;
constexpr size_t kMaxMatch = 258;
constexpr int kHashBits = 15;
constexpr size_t kHashSize = size_t{1} << kHashBits;
constexpr int kChainLimit = 32;
constexpr int32_t kNil = -1;

struct Token {
  bool is_match;
  uint8_t literal;
  size_t length;
  size_t dist;
};

inline size_t hash3(const Bytes& s, size_t i) {
  uint32_t h = (u32(s[i]) << 10) ^
               (u32(s[i + 1]) << 5) ^
               u32(s[i + 2]);
  return h & (kHashSize - 1);
}

inline std::vector<Token> find_tokens(const Bytes& src) {
  size_t n = src.size();
  std::vector<int32_t> head(kHashSize, kNil);
  std::vector<int32_t> prev(std::max<size_t>(n, 1), kNil);
  std::vector<Token> tokens;
  size_t i = 0;
  while (i < n) {
    size_t best_len = 0, best_dist = 0;
    if (i + kMinMatch <= n) {
      size_t limit = std::min(kMaxMatch, n - i);
      int32_t cand = head[hash3(src, i)];
      int probes = 0;
      while (cand != kNil && probes < kChainLimit) {
        size_t c = sz(cand);
        size_t dist = i - c;
        if (dist > kWindow) break;
        size_t ln = 0;
        while (ln < limit && src[c + ln] == src[i + ln]) ++ln;
        if (ln > best_len) {
          best_len = ln;
          best_dist = dist;
          if (ln == limit) break;
        }
        cand = prev[c];
        ++probes;
      }
    }
    if (best_len >= kMinMatch) {
      for (size_t k = 0; k < best_len; ++k) {
        size_t p = i + k;
        if (p + kMinMatch <= n) {
          size_t h = hash3(src, p);
          prev[p] = head[h];
          head[h] = s32(p);
        }
      }
      tokens.push_back({true, 0, best_len, best_dist});
      i += best_len;
    } else {
      if (i + kMinMatch <= n) {
        size_t h = hash3(src, i);
        prev[i] = head[h];
        head[h] = s32(i);
      }
      tokens.push_back({false, src[i], 0, 0});
      ++i;
    }
  }
  return tokens;
}

inline Bytes encode(const Bytes& src) {
  std::vector<Token> tokens = find_tokens(src);
  Bytes out = varint::put(src.size());
  for (size_t base = 0; base < tokens.size(); base += 8) {
    size_t end = std::min(base + 8, tokens.size());
    uint8_t flag = 0;
    for (size_t k = base; k < end; ++k)
      if (tokens[k].is_match)
        flag = u8(flag | (1u << (7 - (k - base))));
    out.push_back(flag);
    for (size_t k = base; k < end; ++k) {
      const Token& t = tokens[k];
      if (t.is_match) {
        out.push_back(u8(t.length - kMinMatch));
        size_t d = t.dist - 1;
        out.push_back(u8(d & 0xFF));
        out.push_back(u8(d >> 8));
      } else {
        out.push_back(t.literal);
      }
    }
  }
  return out;
}

inline Bytes decode(const Bytes& src) {
  size_t pos = 0;
  size_t n = varint::get_length(src, pos);
  size_t end = src.size();
  Bytes out;
  out.reserve(n);
  while (out.size() < n) {
    if (pos >= end) fail("플래그 바이트가 없다");
    uint8_t flag = src[pos++];
    for (int k = 0; k < 8 && out.size() < n; ++k) {
      if (flag & (1u << (7 - k))) {
        if (pos + 3 > end) fail("일치 토큰이 잘렸다");
        size_t ln = sz(src[pos]) + kMinMatch;
        size_t dist = sz(src[pos + 1]) |
                      (sz(src[pos + 2]) << 8);
        dist += 1;
        pos += 3;
        if (dist > out.size()) fail("거리가 낸 것보다 멀다");
        size_t start = out.size() - dist;
        // 한 바이트씩 앞으로. 거리 1 짜리 긴 일치가 여기 기댄다 —
        // memmove 는 틀린다.
        for (size_t j = 0; j < ln; ++j) out.push_back(out[start + j]);
      } else {
        if (pos >= end) fail("리터럴이 잘렸다");
        out.push_back(src[pos++]);
      }
    }
  }
  if (out.size() != n) fail("푼 길이가 헤더와 다르다");
  if (pos != end) fail("뒤에 남은 바이트가 있다");
  return out;
}

}  // namespace lzss
}  // namespace compresslib

#endif
