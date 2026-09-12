// -*- coding: utf-8 -*-
// DEFLATE 부호기 — SPEC §10.
//
// RFC 가 부호기에 맡긴 선택을 전부 못 박은 것이 이 파일이다. 블록
// 65535, 값을 정확히 세어 가장 작은 것, 같으면 stored → fixed →
// dynamic. 값을 어림하면 언어마다 반올림이 달라져 블록 종류가 갈린다.
#ifndef COMPRESSLIB_DEFLATE_H
#define COMPRESSLIB_DEFLATE_H

#include <algorithm>

#include "bitio.h"
#include "common.h"
#include "deflate_tables.h"
#include "huffman.h"
#include "inflate.h"

namespace compresslib {
namespace deflate {

constexpr size_t kBlockSize = 65535;
constexpr int kHashBits = 15;
constexpr size_t kHashSize = size_t{1} << kHashBits;
constexpr int kChainLimit = 128;
constexpr int32_t kNil = -1;

struct Token {
  bool is_match;
  uint8_t literal;
  size_t length;
  size_t dist;
};

struct ClItem {
  int sym;
  int value;
  int nbits;
};

inline size_t hash3(const Bytes& s, size_t i) {
  uint32_t h = (u32(s[i]) << 10) ^
               (u32(s[i + 1]) << 5) ^
               u32(s[i + 2]);
  return h & (kHashSize - 1);
}

inline std::vector<Token> parse(const Bytes& src) {
  size_t n = src.size();
  std::vector<int32_t> head(kHashSize, kNil);
  std::vector<int32_t> prev(std::max<size_t>(n, 1), kNil);
  std::vector<Token> tokens;

  auto insert = [&](size_t p) {
    if (p + dfl::kMinMatch <= n) {
      size_t h = hash3(src, p);
      prev[p] = head[h];
      head[h] = s32(p);
    }
  };
  auto find = [&](size_t p, size_t& best_len, size_t& best_dist) {
    best_len = 0;
    best_dist = 0;
    if (p + dfl::kMinMatch > n) return;
    size_t limit = std::min(dfl::kMaxMatch, n - p);
    int32_t cand = head[hash3(src, p)];
    int probes = 0;
    while (cand != kNil && probes < kChainLimit) {
      size_t c = sz(cand);
      size_t dist = p - c;
      if (dist > dfl::kMaxDist) break;
      size_t ln = 0;
      while (ln < limit && src[c + ln] == src[p + ln]) ++ln;
      if (ln > best_len) {
        best_len = ln;
        best_dist = dist;
        if (ln == limit) break;
      }
      cand = prev[c];
      ++probes;
    }
  };

  size_t i = 0;
  while (i < n) {
    size_t ln = 0, dist = 0;
    find(i, ln, dist);
    insert(i);
    if (ln >= dfl::kMinMatch) {
      size_t nxt_len = 0, nxt_dist = 0;
      if (i + 1 < n) find(i + 1, nxt_len, nxt_dist);
      if (nxt_len > ln) {                 // 게으른 일치
        tokens.push_back({false, src[i], 0, 0});
        ++i;
        continue;
      }
      for (size_t k = 1; k < ln; ++k) insert(i + k);
      tokens.push_back({true, 0, ln, dist});
      i += ln;
    } else {
      tokens.push_back({false, src[i], 0, 0});
      ++i;
    }
  }
  return tokens;
}

struct Block {
  size_t tok_a, tok_b, in_a, in_b;
};

inline std::vector<Block> split_blocks(
    const std::vector<Token>& tokens) {
  std::vector<Block> blocks;
  size_t tok_start = 0, in_start = 0, cur = 0;
  for (size_t k = 0; k < tokens.size(); ++k) {
    cur += tokens[k].is_match ? tokens[k].length : 1;
    if (cur >= kBlockSize) {
      blocks.push_back({tok_start, k + 1, in_start, in_start + cur});
      tok_start = k + 1;
      in_start += cur;
      cur = 0;
    }
  }
  if (cur || blocks.empty())
    blocks.push_back(
        {tok_start, tokens.size(), in_start, in_start + cur});
  return blocks;
}

inline void freqs_of(const std::vector<Token>& tokens, size_t a,
                     size_t b, std::vector<uint64_t>& lit,
                     std::vector<uint64_t>& dst, size_t& extra) {
  lit.assign(dfl::kLitlenSymbols, 0);
  dst.assign(dfl::kDistSymbols, 0);
  extra = 0;
  for (size_t k = a; k < b; ++k) {
    const Token& t = tokens[k];
    if (t.is_match) {
      int code = dfl::length_code(t.length);
      lit[sz(code)] += 1;
      extra += sz(dfl::kLengthExtra[sz(code - 257)]);
      int dc = dfl::dist_code(t.dist);
      dst[sz(dc)] += 1;
      extra += sz(dfl::kDistExtra[sz(dc)]);
    } else {
      lit[t.literal] += 1;
    }
  }
  lit[dfl::kEndOfBlock] += 1;
}

inline size_t body_bits(const std::vector<uint64_t>& lit,
                        const std::vector<uint64_t>& dst, size_t extra,
                        const std::vector<int>& lit_len,
                        const std::vector<int>& dst_len) {
  size_t bits = extra;
  for (size_t s = 0; s < lit.size(); ++s)
    if (lit[s]) bits += lit[s] * sz(lit_len[s]);
  for (size_t s = 0; s < dst.size(); ++s)
    if (dst[s]) bits += dst[s] * sz(dst_len[s]);
  return bits;
}

inline std::vector<ClItem> cl_encode(const std::vector<int>& lengths) {
  std::vector<ClItem> out;
  size_t i = 0, n = lengths.size();
  while (i < n) {
    int cur = lengths[i];
    size_t run = 1;
    while (i + run < n && lengths[i + run] == cur) ++run;
    if (cur == 0) {
      while (run >= 3) {
        size_t k;
        if (run >= 11) {
          k = std::min<size_t>(run, 138);
          out.push_back({dfl::kClZeroLong, i32(k) - 11, 7});
        } else {
          k = std::min<size_t>(run, 10);
          out.push_back({dfl::kClZeroShort, i32(k) - 3, 3});
        }
        run -= k;
        i += k;
      }
      for (size_t j = 0; j < run; ++j) {
        out.push_back({0, 0, 0});
        ++i;
      }
    } else {
      out.push_back({cur, 0, 0});
      ++i;
      --run;
      while (run >= 3) {
        size_t k = std::min<size_t>(run, 6);
        out.push_back({dfl::kClRepeat, i32(k) - 3, 2});
        run -= k;
        i += k;
      }
      for (size_t j = 0; j < run; ++j) {
        out.push_back({cur, 0, 0});
        ++i;
      }
    }
  }
  return out;
}

inline size_t last_used(const std::vector<int>& lengths) {
  for (size_t s = lengths.size(); s > 0; --s)
    if (lengths[s - 1]) return s;
  return 0;
}

struct DynamicPlan {
  std::vector<int> lit_len, dst_len, cl_len;
  std::vector<ClItem> items;
  size_t hlit = 0, hdist = 0, hclen = 0, bits = 0;

  DynamicPlan(const std::vector<uint64_t>& lit_freq,
              const std::vector<uint64_t>& dst_freq, size_t extra) {
    lit_len = huffman::code_lengths(lit_freq, huffman::kMaxLength);
    dst_len = huffman::code_lengths(dst_freq, huffman::kMaxLength);
    bool any = false;
    for (int l : dst_len) any = any || l;
    if (!any) dst_len[0] = 1;      // 일치가 하나도 없는 블록 (§10.5)
    hlit = std::max<size_t>(257, last_used(lit_len));
    hdist = std::max<size_t>(1, last_used(dst_len));
    std::vector<int> joined(lit_len.begin(),
                            lit_len.begin() + ix(hlit));
    joined.insert(joined.end(), dst_len.begin(),
                  dst_len.begin() + ix(hdist));
    items = cl_encode(joined);
    std::vector<uint64_t> cl_freq(dfl::kClSymbols, 0);
    for (const ClItem& it : items) cl_freq[sz(it.sym)] += 1;
    cl_len = huffman::code_lengths(cl_freq, dfl::kClMaxLength);
    hclen = dfl::kClSymbols;
    while (hclen > 4 &&
           cl_len[sz(dfl::kClOrder[hclen - 1])] == 0)
      --hclen;
    size_t header = 5 + 5 + 4 + 3 * hclen;
    for (const ClItem& it : items)
      header += sz(cl_len[sz(it.sym)] + it.nbits);
    bits = 3 + header +
           body_bits(lit_freq, dst_freq, extra, lit_len, dst_len);
  }
};

inline void write_body(bitio::LsbWriter& w,
                       const std::vector<Token>& tokens, size_t a,
                       size_t b, const std::vector<int>& lit_len,
                       const std::vector<int>& lit_code,
                       const std::vector<int>& dst_len,
                       const std::vector<int>& dst_code) {
  for (size_t k = a; k < b; ++k) {
    const Token& t = tokens[k];
    if (t.is_match) {
      size_t code = sz(dfl::length_code(t.length));
      w.write_code(u64(lit_code[code]), lit_len[code]);
      size_t idx = code - 257;
      if (dfl::kLengthExtra[idx])
        w.write_bits(t.length - sz(dfl::kLengthBase[idx]),
                     dfl::kLengthExtra[idx]);
      size_t dc = sz(dfl::dist_code(t.dist));
      w.write_code(u64(dst_code[dc]), dst_len[dc]);
      if (dfl::kDistExtra[dc])
        w.write_bits(t.dist - sz(dfl::kDistBase[dc]),
                     dfl::kDistExtra[dc]);
    } else {
      w.write_code(u64(lit_code[t.literal]),
                   lit_len[t.literal]);
    }
  }
  size_t eob = dfl::kEndOfBlock;
  w.write_code(u64(lit_code[eob]), lit_len[eob]);
}

inline Bytes deflate_raw(const Bytes& src) {
  bitio::LsbWriter w;
  if (src.empty()) {
    w.write_bits(1, 1);
    w.write_bits(1, 2);
    w.write_code(0, 7);
    w.flush();
    return w.bytes();
  }
  std::vector<Token> tokens = parse(src);
  std::vector<Block> blocks = split_blocks(tokens);
  const std::vector<int>& fixed_lit = dfl::fixed_litlen();
  const std::vector<int>& fixed_dst = dfl::fixed_dist();
  std::vector<int> fixed_code = huffman::canonical_codes(fixed_lit);
  std::vector<int> fixed_dcode = huffman::canonical_codes(fixed_dst);
  std::vector<uint64_t> lit_freq, dst_freq;
  for (size_t k = 0; k < blocks.size(); ++k) {
    const Block& blk = blocks[k];
    int final_block = (k == blocks.size() - 1) ? 1 : 0;
    size_t extra = 0;
    freqs_of(tokens, blk.tok_a, blk.tok_b, lit_freq, dst_freq, extra);
    size_t raw_len = blk.in_b - blk.in_a;
    size_t pad = (8 - ((w.bit_pos() + 3) % 8)) % 8;
    size_t cost_stored = 3 + pad + 32 + 8 * raw_len;
    size_t cost_fixed =
        3 + body_bits(lit_freq, dst_freq, extra, fixed_lit, fixed_dst);
    DynamicPlan plan(lit_freq, dst_freq, extra);
    if (cost_stored <= cost_fixed && cost_stored <= plan.bits) {
      w.write_bits(u64(final_block), 1);
      w.write_bits(0, 2);
      w.align();
      w.write_bits(raw_len, 16);
      w.write_bits(raw_len ^ 0xFFFF, 16);
      for (size_t j = blk.in_a; j < blk.in_b; ++j)
        w.write_bits(src[j], 8);
      continue;
    }
    w.write_bits(u64(final_block), 1);
    if (cost_fixed <= plan.bits) {
      w.write_bits(1, 2);
      write_body(w, tokens, blk.tok_a, blk.tok_b, fixed_lit, fixed_code,
                 fixed_dst, fixed_dcode);
      continue;
    }
    w.write_bits(2, 2);
    w.write_bits(plan.hlit - 257, 5);
    w.write_bits(plan.hdist - 1, 5);
    w.write_bits(plan.hclen - 4, 4);
    for (size_t i = 0; i < plan.hclen; ++i)
      w.write_bits(u64(
                       plan.cl_len[sz(dfl::kClOrder[i])]), 3);
    std::vector<int> cl_code = huffman::canonical_codes(plan.cl_len);
    for (const ClItem& it : plan.items) {
      size_t s = sz(it.sym);
      w.write_code(u64(cl_code[s]), plan.cl_len[s]);
      if (it.nbits) w.write_bits(u64(it.value), it.nbits);
    }
    write_body(w, tokens, blk.tok_a, blk.tok_b, plan.lit_len,
               huffman::canonical_codes(plan.lit_len), plan.dst_len,
               huffman::canonical_codes(plan.dst_len));
  }
  w.flush();
  return w.bytes();
}

inline Bytes encode(const Bytes& src) { return deflate_raw(src); }
inline Bytes decode(const Bytes& src) {
  return inflate::inflate_raw(src);
}

}  // namespace deflate
}  // namespace compresslib

#endif
