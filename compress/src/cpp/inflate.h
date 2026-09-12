// -*- coding: utf-8 -*-
// inflate — RFC 1951 복호기 (SPEC §10.7).
//
// 받아 주면 안 되는 것을 일부러 나열한다. 손상된 파일을 조용히 넘기는
// 복호기는 압축에서 특히 위험하다 — 아무거나 그럴듯한 바이트가 나온다.
#ifndef COMPRESSLIB_INFLATE_H
#define COMPRESSLIB_INFLATE_H

#include "bitio.h"
#include "common.h"
#include "deflate_tables.h"
#include "huffman.h"

namespace compresslib {
namespace inflate {

inline huffman::Decoder make_table(const std::vector<int>& lengths) {
  huffman::check_complete(lengths);
  return huffman::Decoder(lengths);
}

inline void read_body(bitio::LsbReader& r, Bytes& out,
                      const huffman::Decoder& litlen,
                      const huffman::Decoder& dist) {
  for (;;) {
    int sym = litlen.read(r);
    if (sym < 256) {
      out.push_back(u8(sym));
      continue;
    }
    if (sym == dfl::kEndOfBlock) return;
    size_t idx = sz(sym - 257);
    if (idx >= dfl::kLengthBase.size()) fail("없는 길이 부호");
    size_t length = sz(dfl::kLengthBase[idx]) +
                    sz(r.read_bits(dfl::kLengthExtra[idx]));
    int dcode = dist.read(r);
    if (dcode >= i32(dfl::kDistSymbols)) fail("쓰이지 않는 거리 부호");
    size_t dc = sz(dcode);
    size_t d = sz(dfl::kDistBase[dc]) +
               sz(r.read_bits(dfl::kDistExtra[dc]));
    if (d > out.size()) fail("거리가 지금까지 낸 것보다 멀다");
    size_t start = out.size() - d;
    for (size_t k = 0; k < length; ++k) out.push_back(out[start + k]);
  }
}

inline void read_dynamic(bitio::LsbReader& r, std::vector<int>& lit,
                         std::vector<int>& dst) {
  size_t hlit = sz(r.read_bits(5)) + 257;
  size_t hdist = sz(r.read_bits(5)) + 1;
  size_t hclen = sz(r.read_bits(4)) + 4;
  if (hlit > dfl::kLitlenSymbols || hdist > dfl::kDistSymbols)
    fail("HLIT/HDIST 가 알파벳을 넘는다");
  std::vector<int> cl_lengths(dfl::kClSymbols, 0);
  for (size_t i = 0; i < hclen; ++i)
    cl_lengths[sz(dfl::kClOrder[i])] =
        i32(r.read_bits(3));
  huffman::Decoder cl = make_table(cl_lengths);

  std::vector<int> lengths;
  size_t want = hlit + hdist;
  lengths.reserve(want);
  while (lengths.size() < want) {
    int sym = cl.read(r);
    if (sym < 16) {
      lengths.push_back(sym);
    } else if (sym == dfl::kClRepeat) {
      if (lengths.empty()) fail("부호 16 이 맨 앞에 왔다");
      int prev = lengths.back();
      int n = i32(r.read_bits(2)) + 3;
      for (int i = 0; i < n; ++i) lengths.push_back(prev);
    } else if (sym == dfl::kClZeroShort) {
      int n = i32(r.read_bits(3)) + 3;
      lengths.insert(lengths.end(), sz(n), 0);
    } else {
      int n = i32(r.read_bits(7)) + 11;
      lengths.insert(lengths.end(), sz(n), 0);
    }
  }
  if (lengths.size() != want) fail("부호 길이 되풀이가 표 끝을 넘었다");
  lit.assign(lengths.begin(), lengths.begin() + ix(hlit));
  dst.assign(lengths.begin() + ix(hlit), lengths.end());
}

inline Bytes inflate_raw(const Bytes& src) {
  bitio::LsbReader r(src);
  Bytes out;
  for (;;) {
    int final_block = r.read_bit();
    int btype = i32(r.read_bits(2));
    if (btype == 0) {
      r.align();
      size_t p = r.pos();
      if (p + 4 > src.size()) fail("stored 블록 머리가 잘렸다");
      size_t ln = sz(src[p]) |
                  (sz(src[p + 1]) << 8);
      size_t nln = sz(src[p + 2]) |
                   (sz(src[p + 3]) << 8);
      p += 4;
      if (ln != (nln ^ 0xFFFF)) fail("NLEN 이 LEN 의 보수가 아니다");
      if (p + ln > src.size()) fail("stored 블록 몸통이 잘렸다");
      out.insert(out.end(), src.begin() + ix(p),
                 src.begin() + ix(p + ln));
      r.set_pos(p + ln);
    } else if (btype == 1) {
      static const huffman::Decoder lit(dfl::fixed_litlen());
      static const huffman::Decoder dst(dfl::fixed_dist());
      read_body(r, out, lit, dst);
    } else if (btype == 2) {
      std::vector<int> lit_lengths, dst_lengths;
      read_dynamic(r, lit_lengths, dst_lengths);
      huffman::Decoder lit = make_table(lit_lengths);
      huffman::Decoder dst = make_table(dst_lengths);
      read_body(r, out, lit, dst);
    } else {
      fail("BTYPE 11 은 없는 블록 종류다");
    }
    if (final_block) return out;
  }
}

}  // namespace inflate
}  // namespace compresslib

#endif
