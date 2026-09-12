// -*- coding: utf-8 -*-
// 캐노니컬 허프만 — SPEC §5.
//
// 트리를 만들지 않는다. 최적 길이 벡터는 하나가 아니어서(1,1,1,1 은 두
// 벌이 다 최적) 트리를 만들면 우선순위 큐의 동점 처리가 어느 쪽을
// 고를지 정하는데, 그 처리는 언어마다 다르다. package–merge 의 정렬 키
// (무게, 종류, 순번) 가 동점 처리 전부이고, 그 키 덕분에 결과가 빈도
// 벡터만의 함수가 된다.
#ifndef COMPRESSLIB_HUFFMAN_H
#define COMPRESSLIB_HUFFMAN_H

#include <algorithm>

#include "bitio.h"
#include "common.h"
#include "varint.h"

namespace compresslib {
namespace huffman {

constexpr int kMaxLength = 15;
constexpr int kAlphabet = 256;
constexpr size_t kTableBytes = kAlphabet / 2;

struct Coin {
  uint64_t weight;
  int kind;   // 0 = 기호 동전, 1 = 꾸러미 (무게가 같으면 기호가 앞선다)
  int rank;
  std::vector<int> syms;
};

inline bool coin_less(const Coin& a, const Coin& b) {
  if (a.weight != b.weight) return a.weight < b.weight;
  if (a.kind != b.kind) return a.kind < b.kind;
  return a.rank < b.rank;
}

inline std::vector<int> code_lengths(const std::vector<uint64_t>& freqs,
                                     int limit = kMaxLength) {
  std::vector<std::pair<uint64_t, int>> used;
  for (size_t s = 0; s < freqs.size(); ++s)
    if (freqs[s]) used.emplace_back(freqs[s], i32(s));
  std::sort(used.begin(), used.end());
  std::vector<int> lengths(freqs.size(), 0);
  size_t m = used.size();
  if (m == 0) return lengths;
  if (m == 1) {
    lengths[sz(used[0].second)] = 1;
    return lengths;
  }
  if (limit < 63 && m > (size_t{1} << limit))
    fail("기호가 길이 제한에 안 담긴다");

  std::vector<Coin> coins;
  coins.reserve(m);
  for (size_t j = 0; j < m; ++j)
    coins.push_back({used[j].first, 0, i32(j), {used[j].second}});
  std::vector<Coin> level = coins;
  for (int round = 0; round < limit - 1; ++round) {
    std::vector<Coin> packed;
    packed.reserve(level.size() / 2);
    for (size_t i = 0; i + 1 < level.size(); i += 2) {
      Coin c;
      c.weight = level[i].weight + level[i + 1].weight;
      c.kind = 1;
      c.rank = i32(packed.size());
      c.syms = level[i].syms;
      c.syms.insert(c.syms.end(), level[i + 1].syms.begin(),
                    level[i + 1].syms.end());
      packed.push_back(std::move(c));
    }
    level = packed;
    level.insert(level.end(), coins.begin(), coins.end());
    std::sort(level.begin(), level.end(), coin_less);
  }
  size_t take = 2 * m - 2;
  for (size_t i = 0; i < take && i < level.size(); ++i)
    for (int s : level[i].syms) lengths[sz(s)] += 1;
  return lengths;
}

inline std::vector<int> canonical_codes(
    const std::vector<int>& lengths) {
  std::vector<int> bl_count(kMaxLength + 1, 0);
  for (int l : lengths) {
    if (l) {
      if (l > kMaxLength) fail("부호 길이가 상한을 넘는다");
      bl_count[sz(l)] += 1;
    }
  }
  std::vector<int> next_code(kMaxLength + 2, 0);
  int code = 0;
  for (int bits = 1; bits <= kMaxLength; ++bits) {
    code = (code + bl_count[sz(bits - 1)]) << 1;
    next_code[sz(bits)] = code;
  }
  std::vector<int> codes(lengths.size(), 0);
  for (size_t s = 0; s < lengths.size(); ++s) {
    int l = lengths[s];
    if (!l) continue;
    if (next_code[sz(l)] >= (1 << l)) fail("부호표가 넘친다");
    codes[s] = next_code[sz(l)]++;
  }
  return codes;
}

// 크래프트 합이 1 인지. 예외는 **기호 하나짜리 표** — 길이 1 하나라 늘
// 합이 1/2 이고, zeros_64k 처럼 한 바이트만 있는 파일에서 반드시
// 나온다.
inline void check_complete(const std::vector<int>& lengths,
                           int max_length = kMaxLength) {
  uint64_t total = 0;
  int used = 0, only = 0;
  for (int l : lengths) {
    if (l) {
      total += uint64_t{1} << (max_length - l);
      ++used;
      only = l;
    }
  }
  uint64_t full = uint64_t{1} << max_length;
  if (total > full) fail("부호표가 넘친다 (크래프트 합 > 1)");
  if (total < full && !(used == 1 && only == 1))
    fail("부호표가 모자란다 (크래프트 합 < 1)");
}

// 캐노니컬 복호기 — 트리를 안 만든다. 길이별 첫 부호와 첫 자리만 있으면
// 비트를 하나씩 받아 가며 판정할 수 있다.
class Decoder {
 public:
  explicit Decoder(const std::vector<int>& lengths,
                   int max_length = kMaxLength)
      : max_length_(max_length) {
    std::vector<std::pair<int, int>> pairs;
    for (size_t s = 0; s < lengths.size(); ++s)
      if (lengths[s]) pairs.emplace_back(lengths[s], i32(s));
    std::sort(pairs.begin(), pairs.end());
    symbols_.reserve(pairs.size());
    count_.assign(sz(max_length) + 1, 0);
    for (auto& p : pairs) {
      symbols_.push_back(p.second);
      count_[sz(p.first)] += 1;
    }
    first_code_.assign(sz(max_length) + 2, 0);
    first_index_.assign(sz(max_length) + 2, 0);
    int code = 0, index = 0;
    for (int l = 1; l <= max_length; ++l) {
      code = (code + count_[sz(l - 1)]) << 1;
      first_code_[sz(l)] = code;
      first_index_[sz(l)] = index;
      index += count_[sz(l)];
    }
  }
  template <class Reader>
  int read(Reader& r) const {
    int code = 0;
    for (int l = 1; l <= max_length_; ++l) {
      code = (code << 1) | r.read_bit();
      int off = code - first_code_[sz(l)];
      if (count_[sz(l)] && off < count_[sz(l)])
        return symbols_[sz(
            first_index_[sz(l)] + off)];
    }
    fail("부호표에 없는 비트열");
  }

 private:
  int max_length_ = kMaxLength;
  std::vector<int> symbols_, count_, first_code_, first_index_;
};

inline int nibble(const Bytes& table, int sym) {
  uint8_t b = table[sz(sym >> 1)];
  return (sym & 1) ? (b & 0x0F) : (b >> 4);
}

inline Bytes pack_table(const std::vector<int>& lengths) {
  Bytes table(kTableBytes, 0);
  for (int s = 0; s < kAlphabet; ++s) {
    uint8_t v = u8(lengths[sz(s)] & 0x0F);
    if (s & 1)
      table[sz(s >> 1)] |= v;
    else
      table[sz(s >> 1)] |= u8(v << 4);
  }
  return table;
}

inline Bytes encode(const Bytes& src) {
  if (src.empty()) return varint::put(0);
  std::vector<uint64_t> freqs(kAlphabet, 0);
  for (uint8_t b : src) freqs[b] += 1;
  std::vector<int> lengths = code_lengths(freqs);
  std::vector<int> codes = canonical_codes(lengths);
  bitio::MsbWriter w;
  for (uint8_t b : src)
    w.write_bits(u64(codes[b]), lengths[b]);
  w.flush();
  Bytes out = varint::put(src.size());
  Bytes table = pack_table(lengths);
  out.insert(out.end(), table.begin(), table.end());
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
  if (src.size() < pos + kTableBytes) fail("부호 길이 표가 잘렸다");
  Bytes table(src.begin() + ix(pos),
              src.begin() + ix(pos + kTableBytes));
  std::vector<int> lengths(kAlphabet, 0);
  for (int s = 0; s < kAlphabet; ++s) lengths[sz(s)] = nibble(table, s);
  check_complete(lengths);
  Decoder dec(lengths);
  bitio::MsbReader r(src, pos + kTableBytes);
  Bytes out;
  out.reserve(n);
  for (size_t i = 0; i < n; ++i)
    out.push_back(u8(dec.read(r)));
  return out;
}

}  // namespace huffman
}  // namespace compresslib

#endif
