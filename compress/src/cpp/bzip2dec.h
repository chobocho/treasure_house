// -*- coding: utf-8 -*-
// bzip2 복호기 — SPEC §15.
//
// bzip2 가 쓰는 조각은 이미 다 있다. BWT·MTF·0런·캐노니컬 허프만.
// bzip2 가 더한 것은 **조립** 이라, 부호기는 안 만든다 — 진짜 bzip2 가
// 만든 파일을 푸는 편이 훨씬 센 주장이다.
//
// 가장 잘 속는 자리는 CRC 다. bzip2 의 CRC-32 는 gzip 것과 다항식은
// 같아도 **반사가 없다.** gzip 표를 그대로 쓰면 빈 입력만 맞는다
// (§15.6).
#ifndef COMPRESSLIB_BZIP2DEC_H
#define COMPRESSLIB_BZIP2DEC_H

#include <array>

#include "bwt.h"
#include "common.h"
#include "huffman.h"

namespace compresslib {
namespace bzip2dec {

constexpr uint64_t kBlockMagic = 0x314159265359ull;
constexpr uint64_t kEndMagic = 0x177245385090ull;
constexpr int kMaxGroups = 6;
constexpr int kGroupSize = 50;
constexpr int kMaxCodeLen = 20;
constexpr int kRunA = 0;
constexpr int kRunB = 1;

// 반사 없는 CRC-32/BZIP2 표. 다항식 0x04C11DB7 을 위에서부터 민다.
inline const std::array<uint32_t, 256>& crc_table() {
  static const std::array<uint32_t, 256> t = [] {
    std::array<uint32_t, 256> table{};
    for (uint32_t i = 0; i < 256; ++i) {
      uint32_t c = i << 24;
      for (int k = 0; k < 8; ++k) {
        c = (c & 0x80000000u) ? ((c << 1) ^ 0x04C11DB7u) : (c << 1);
      }
      table[i] = c;
    }
    return table;
  }();
  return t;
}

inline uint32_t crc32_bzip2(const Bytes& data) {
  const auto& t = crc_table();
  uint32_t c = 0xFFFFFFFFu;
  for (uint8_t b : data) c = t[((c >> 24) ^ b) & 0xFF] ^ (c << 8);
  return c ^ 0xFFFFFFFFu;
}

// MSB 먼저. bzip2 는 48비트 매직을 읽어야 해서 넓은 읽기가 필요하다.
class BitReader {
 public:
  BitReader(const Bytes& src, size_t pos) : src_(src), pos_(pos) {}
  int read_bit() {
    if (n_ == 0) {
      if (pos_ >= src_.size()) fail("bzip2 스트림이 바닥났다");
      buf_ = src_[pos_++];
      n_ = 8;
    }
    --n_;
    return (buf_ >> n_) & 1;
  }
  uint64_t read_bits(int count) {
    uint64_t v = 0;
    for (int i = 0; i < count; ++i) v = (v << 1) | u64(read_bit());
    return v;
  }

 private:
  const Bytes& src_;
  size_t pos_;
  uint8_t buf_ = 0;
  int n_ = 0;
};

// 같은 바이트 넷 뒤의 한 바이트는 "더 붙일 개수" 다 (§15.5).
inline Bytes rle1_decode(const Bytes& src) {
  Bytes out;
  size_t i = 0, n = src.size();
  while (i < n) {
    uint8_t b = src[i];
    size_t run = 1;
    while (run < 4 && i + run < n && src[i + run] == b) ++run;
    out.insert(out.end(), run, b);
    i += run;
    if (run == 4) {
      if (i >= n) fail("RLE1 의 개수 바이트가 없다");
      out.insert(out.end(), src[i], b);
      ++i;
    }
  }
  return out;
}

inline std::vector<int> read_symbol_map(BitReader& r) {
  std::vector<int> used;
  uint64_t groups = r.read_bits(16);
  for (int g = 0; g < 16; ++g) {
    if (groups & (uint64_t{1} << (15 - g))) {
      uint64_t bits = r.read_bits(16);
      for (int k = 0; k < 16; ++k) {
        if (bits & (uint64_t{1} << (15 - k))) {
          used.push_back(g * 16 + k);
        }
      }
    }
  }
  if (used.empty()) fail("기호 지도가 비었다");
  return used;
}

// 단항으로 적힌 MTF 선택자. 값이 곧 "몇 번째 표" 다.
inline std::vector<int> read_selectors(BitReader& r, int n_groups,
                                       int n_selectors) {
  std::vector<int> mtf(sz(n_groups));
  for (int i = 0; i < n_groups; ++i) mtf[sz(i)] = i;
  std::vector<int> out;
  out.reserve(sz(n_selectors));
  for (int i = 0; i < n_selectors; ++i) {
    int j = 0;
    while (r.read_bit()) {
      if (++j >= n_groups) fail("선택자가 표 개수를 넘는다");
    }
    int v = mtf[sz(j)];
    mtf.erase(mtf.begin() + ix(j));
    mtf.insert(mtf.begin(), v);
    out.push_back(v);
  }
  return out;
}

inline std::vector<huffman::Decoder> read_tables(BitReader& r,
                                                 int n_groups,
                                                 int alpha_size) {
  std::vector<huffman::Decoder> tables;
  for (int g = 0; g < n_groups; ++g) {
    int length = i32(r.read_bits(5));
    std::vector<int> lengths;
    lengths.reserve(sz(alpha_size));
    for (int s = 0; s < alpha_size; ++s) {
      for (;;) {
        if (length < 1 || length > kMaxCodeLen) {
          fail("부호 길이가 범위 밖이다");
        }
        if (!r.read_bit()) break;
        length += r.read_bit() ? -1 : 1;
      }
      lengths.push_back(length);
    }
    huffman::check_complete(lengths, kMaxCodeLen);
    tables.emplace_back(lengths, kMaxCodeLen);
  }
  return tables;
}

// 허프만 → MTF 지표 열. RUNA/RUNB 는 여기서 0 의 런으로 편다.
inline std::vector<int> read_block_symbols(
    BitReader& r, const std::vector<huffman::Decoder>& tables,
    const std::vector<int>& selectors, int alpha_size, size_t limit) {
  int eob = alpha_size - 1;
  std::vector<int> out;
  size_t group = 0;
  int left = 0;
  const huffman::Decoder* dec = nullptr;
  uint64_t run = 0, weight = 1;
  for (;;) {
    if (left == 0) {
      if (group >= selectors.size()) fail("선택자가 모자란다");
      dec = &tables[sz(selectors[group])];
      ++group;
      left = kGroupSize;
    }
    --left;
    int sym = dec->read(r);
    if (sym <= kRunB) {
      run += u64(sym + 1) * weight;
      weight <<= 1;
      if (run > limit) fail("0 런이 블록 크기를 넘는다");
      continue;
    }
    if (run) {
      out.insert(out.end(), sz(run), 0);
      run = 0;
      weight = 1;
    }
    if (sym == eob) return out;
    out.push_back(sym - 1);
    if (out.size() > limit) fail("블록이 상한을 넘는다");
  }
}

// 쓰인 값들만 놓고 MTF 를 되돌린다 — 기호 지도가 여기서 값을 한다.
inline Bytes inverse_mtf(const std::vector<int>& indices,
                         const std::vector<int>& used) {
  std::vector<int> table = used;
  Bytes out;
  out.reserve(indices.size());
  for (int i : indices) {
    if (i >= i32(table.size())) fail("MTF 지표가 알파벳을 넘는다");
    int v = table[sz(i)];
    out.push_back(u8(v));
    if (i) {
      table.erase(table.begin() + ix(i));
      table.insert(table.begin(), v);
    }
  }
  return out;
}

inline Bytes decode(const Bytes& src) {
  if (src.size() < 4 || src[0] != 'B' || src[1] != 'Z' ||
      src[2] != 'h') {
    fail("bzip2 매직이 아니다");
  }
  int level = i32(src[3]) - 0x30;
  if (level < 1 || level > 9) fail("블록 크기 등급이 1~9 가 아니다");
  size_t limit = sz(level) * 100000;
  BitReader r(src, 4);
  Bytes out;
  uint32_t combined = 0;
  for (;;) {
    uint64_t magic = r.read_bits(48);
    if (magic == kEndMagic) {
      uint32_t want = u32(r.read_bits(32));
      if (want != combined) fail("합친 CRC 가 다르다");
      return out;
    }
    if (magic != kBlockMagic) fail("블록 매직이 아니다");
    uint32_t block_crc = u32(r.read_bits(32));
    if (r.read_bit()) fail("무작위화된 블록은 지원하지 않는다");
    uint32_t orig_ptr = u32(r.read_bits(24));
    std::vector<int> used = read_symbol_map(r);
    int alpha_size = i32(used.size()) + 2;
    int n_groups = i32(r.read_bits(3));
    if (n_groups < 2 || n_groups > kMaxGroups) {
      fail("표 개수가 2~6 이 아니다");
    }
    int n_selectors = i32(r.read_bits(15));
    std::vector<int> selectors =
        read_selectors(r, n_groups, n_selectors);
    std::vector<huffman::Decoder> tables =
        read_tables(r, n_groups, alpha_size);
    std::vector<int> indices =
        read_block_symbols(r, tables, selectors, alpha_size, limit);
    Bytes l_column = inverse_mtf(indices, used);
    if (orig_ptr >= l_column.size()) fail("origPtr 가 블록 밖이다");
    Bytes block = rle1_decode(bwt::inverse_block(l_column, orig_ptr));
    if (crc32_bzip2(block) != block_crc) fail("블록 CRC 가 다르다");
    combined = ((combined << 1) | (combined >> 31)) ^ block_crc;
    out.insert(out.end(), block.begin(), block.end());
  }
}

}  // namespace bzip2dec
}  // namespace compresslib

#endif
