// -*- coding: utf-8 -*-
// LZMA1 복호기 — SPEC §16.
//
// §8 의 레인지 코더를 LZMA 것으로 쓴 이유가 이 파일이다. 같은 코더에
// LZMA 의 문맥 모델만 얹으면 진짜 xz 가 만든 파일이 풀린다.
//
// 읽는 것은 LZMA1 "alone" 형식이다. .xz 컨테이너는 다른 틀이고 12부에서
// 말로만 다룬다 — "LZMA 를 푼다" 와 ".xz 를 푼다" 는 다른 주장이다.
#ifndef COMPRESSLIB_LZMADEC_H
#define COMPRESSLIB_LZMADEC_H

#include <algorithm>

#include "common.h"
#include "rangecoder.h"

namespace compresslib {
namespace lzmadec {

constexpr int kNumStates = 12;
constexpr int kNumPosBitsMax = 4;
constexpr int kNumLenToPosStates = 4;
constexpr int kNumAlignBits = 4;
constexpr int kEndPosModelIndex = 14;
constexpr int kNumFullDistances = 1 << (kEndPosModelIndex >> 1);
constexpr int kMatchMinLen = 2;
constexpr uint64_t kUnknownSize = 0xFFFFFFFFFFFFFFFFull;
constexpr uint32_t kEndMarker = 0xFFFFFFFFu;
constexpr size_t kMaxOutput = size_t{1} << 32;

using Probs = std::vector<uint16_t>;

inline Probs make_probs(size_t n) {
  return Probs(n, rangecoder::kProbInit);
}

// 위에서부터 내려가는 이진 트리. 결과는 num_bits 짜리 값.
inline int bit_tree(rangecoder::Decoder& dec, Probs& probs,
                    size_t offset, int num_bits) {
  int m = 1;
  for (int i = 0; i < num_bits; ++i) {
    m = (m << 1) + dec.decode_bit(probs, offset + sz(m));
  }
  return m - (1 << num_bits);
}

// 같은 트리인데 비트를 **거꾸로** 모은다 — 거리의 아래 비트가 이렇다.
inline uint32_t bit_tree_reverse(rangecoder::Decoder& dec, Probs& probs,
                                 size_t offset, int num_bits) {
  int m = 1;
  uint32_t sym = 0;
  for (int i = 0; i < num_bits; ++i) {
    int bit = dec.decode_bit(probs, offset + sz(m));
    m = (m << 1) + bit;
    sym |= u32(bit) << i;
  }
  return sym;
}

// 길이 복호기. 2..273 을 세 구간(8+8+256)으로 나눠 적는다.
struct LengthCoder {
  Probs choice = make_probs(2);
  Probs low, mid;
  Probs high = make_probs(256);

  explicit LengthCoder(int pos_states)
      : low(make_probs(sz(pos_states) * 8)),
        mid(make_probs(sz(pos_states) * 8)) {}

  int decode(rangecoder::Decoder& dec, int pos_state) {
    if (dec.decode_bit(choice, 0) == 0) {
      return bit_tree(dec, low, sz(pos_state) * 8, 3);
    }
    if (dec.decode_bit(choice, 1) == 0) {
      return 8 + bit_tree(dec, mid, sz(pos_state) * 8, 3);
    }
    return 16 + bit_tree(dec, high, 0, 8);
  }
};

struct Header {
  int lc, lp, pb;
  uint32_t dict_size;
  uint64_t size;
  size_t pos;
};

inline Header parse_header(const Bytes& src) {
  if (src.size() < 13) fail("LZMA 머리가 너무 짧다");
  uint32_t prop = src[0];
  if (prop >= 9 * 5 * 5) fail("속성 바이트가 범위를 넘는다");
  Header h{};
  h.lc = i32(prop % 9);
  uint32_t rest = prop / 9;
  h.lp = i32(rest % 5);
  h.pb = i32(rest / 5);
  h.dict_size = 0;
  for (int i = 0; i < 4; ++i) {
    h.dict_size |= u32(src[sz(1 + i)]) << (8 * i);
  }
  h.size = 0;
  for (int i = 0; i < 8; ++i) h.size |= u64(src[sz(5 + i)]) << (8 * i);
  if (h.size != kUnknownSize && h.size > kMaxOutput) {
    fail("원본 길이가 너무 크다");
  }
  h.pos = 13;
  return h;
}

inline Bytes decode(const Bytes& src) {
  Header h = parse_header(src);
  rangecoder::Decoder dec(src, h.pos);
  int pos_states = 1 << h.pb;
  size_t pos_mask = sz(pos_states) - 1;
  size_t lp_mask = (size_t{1} << h.lp) - 1;

  Probs is_match = make_probs(sz(kNumStates) << kNumPosBitsMax);
  Probs is_rep = make_probs(kNumStates);
  Probs is_rep_g0 = make_probs(kNumStates);
  Probs is_rep_g1 = make_probs(kNumStates);
  Probs is_rep_g2 = make_probs(kNumStates);
  Probs is_rep0_long = make_probs(sz(kNumStates) << kNumPosBitsMax);
  Probs pos_slot = make_probs(sz(kNumLenToPosStates) * 64);
  Probs spec_pos =
      make_probs(sz(kNumFullDistances - kEndPosModelIndex + 1));
  Probs align_probs = make_probs(size_t{1} << kNumAlignBits);
  Probs literal = make_probs(size_t{0x300} << (h.lc + h.lp));
  LengthCoder len_coder(pos_states);
  LengthCoder rep_len_coder(pos_states);

  Bytes out;
  int state = 0;
  uint32_t rep0 = 0, rep1 = 0, rep2 = 0, rep3 = 0;

  while (h.size == kUnknownSize || out.size() < h.size) {
    size_t pos_state = out.size() & pos_mask;
    size_t midx = (sz(state) << kNumPosBitsMax) + pos_state;
    int length;
    if (dec.decode_bit(is_match, midx) == 0) {
      uint32_t prev = out.empty() ? 0u : out.back();
      size_t lit_state =
          ((out.size() & lp_mask) << h.lc) + sz(prev >> (8 - h.lc));
      size_t base = 0x300 * lit_state;
      int symbol = 1;
      if (state >= 7) {
        // 일치 뒤의 리터럴 — 앞 일치의 같은 자리 바이트에 견준다
        if (rep0 + 1 > out.size()) fail("거리가 낸 것보다 멀다");
        uint32_t match_byte = out[out.size() - sz(rep0) - 1];
        while (symbol < 0x100) {
          int match_bit = i32((match_byte >> 7) & 1);
          match_byte = (match_byte << 1) & 0xFF;
          int bit = dec.decode_bit(
              literal, base + sz((1 + match_bit) << 8) + sz(symbol));
          symbol = (symbol << 1) | bit;
          if (match_bit != bit) break;
        }
      }
      while (symbol < 0x100) {
        symbol =
            (symbol << 1) | dec.decode_bit(literal, base + sz(symbol));
      }
      out.push_back(u8(symbol));
      state = state < 4 ? 0 : (state < 10 ? state - 3 : state - 6);
      continue;
    }

    if (dec.decode_bit(is_rep, sz(state))) {
      // 지난 거리 넷 가운데 하나를 다시 쓴다 (§16.4)
      if (out.empty()) fail("첫 기호가 되풀이 일치다");
      if (dec.decode_bit(is_rep_g0, sz(state)) == 0) {
        if (dec.decode_bit(is_rep0_long, midx) == 0) {
          state = state < 7 ? 9 : 11;
          if (rep0 + 1 > out.size()) fail("거리가 낸 것보다 멀다");
          out.push_back(out[out.size() - sz(rep0) - 1]);
          continue;
        }
      } else {
        uint32_t dist;
        if (dec.decode_bit(is_rep_g1, sz(state)) == 0) {
          dist = rep1;
        } else {
          if (dec.decode_bit(is_rep_g2, sz(state)) == 0) {
            dist = rep2;
          } else {
            dist = rep3;
            rep3 = rep2;
          }
          rep2 = rep1;
        }
        rep1 = rep0;
        rep0 = dist;
      }
      length = rep_len_coder.decode(dec, i32(pos_state)) + kMatchMinLen;
      state = state < 7 ? 8 : 11;
    } else {
      rep3 = rep2;
      rep2 = rep1;
      rep1 = rep0;
      length = len_coder.decode(dec, i32(pos_state)) + kMatchMinLen;
      state = state < 7 ? 7 : 10;
      int slot_state =
          std::min(length - kMatchMinLen, kNumLenToPosStates - 1);
      int slot = bit_tree(dec, pos_slot, sz(slot_state) * 64, 6);
      if (slot < 4) {
        rep0 = u32(slot);
      } else {
        int direct = (slot >> 1) - 1;
        rep0 = u32(2 | (slot & 1)) << direct;
        if (slot < kEndPosModelIndex) {
          rep0 += bit_tree_reverse(dec, spec_pos,
                                   sz(rep0) - sz(slot), direct);
        } else {
          rep0 += dec.decode_direct_bits(direct - kNumAlignBits)
                  << kNumAlignBits;
          rep0 += bit_tree_reverse(dec, align_probs, 0, kNumAlignBits);
        }
        if (rep0 == kEndMarker) break;
      }
    }

    // 거리 검사는 한 곳에서만 한다 — 새 일치든 되풀이 일치든 같다.
    if (sz(rep0) >= out.size()) fail("거리가 지금까지 낸 것보다 멀다");
    size_t start = out.size() - sz(rep0) - 1;
    // 한 바이트씩 앞으로. 거리 1 짜리 긴 일치가 여기 기댄다.
    for (int j = 0; j < length; ++j) out.push_back(out[start + sz(j)]);
    if (out.size() > kMaxOutput) fail("푼 길이가 상한을 넘는다");
  }

  if (h.size != kUnknownSize && out.size() != h.size) {
    fail("푼 길이가 머리와 다르다");
  }
  return out;
}

}  // namespace lzmadec
}  // namespace compresslib

#endif
