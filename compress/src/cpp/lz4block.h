// -*- coding: utf-8 -*-
// LZ4 — SPEC §14.
//
// LZ77 인데 **엔트로피 부호가 아예 없다.** 리터럴과 일치를 바이트로
// 그냥 적는다. DEFLATE 보다 덜 줄고 몇 배 빨리 풀린다.
//
// 꼬리 규칙 둘: 마지막 5바이트는 반드시 리터럴, 일치는 끝에서 12바이트
// 안쪽에서 시작 금지. 지키지 않으면 진짜 lz4 가 거절한다.
#ifndef COMPRESSLIB_LZ4BLOCK_H
#define COMPRESSLIB_LZ4BLOCK_H

#include <algorithm>

#include "common.h"
#include "varint.h"

namespace compresslib {
namespace lz4block {

constexpr size_t kMinMatch = 4;
constexpr size_t kLastLiterals = 5;
constexpr size_t kMfLimit = 12;
constexpr int kHashLog = 12;
constexpr size_t kHashSize = size_t{1} << kHashLog;
constexpr uint32_t kHashMul = 2654435761u;
constexpr size_t kMaxOffset = 65535;

inline void put_lsic(Bytes& out, size_t v) {
  while (v >= 255) {
    out.push_back(255);
    v -= 255;
  }
  out.push_back(u8(v));
}

// 고리를 묶는 것은 입력 자신이다 — 이어짐 바이트가 남은 것보다 많을 수
// 없다. 고정 상한은 솔깃하고 틀린다 (SPEC §14.3).
inline size_t get_lsic(const Bytes& src, size_t& pos) {
  uint64_t total = 0;
  while (pos < src.size()) {
    uint8_t b = src[pos++];
    total += b;
    if (b != 255) {
      if (total > varint::kMaxLength) fail("LSIC 값이 너무 크다");
      return sz(total);
    }
  }
  fail("LSIC 가 잘렸다");
}

inline size_t hash4(const Bytes& s, size_t i) {
  uint32_t v = u32(s[i]) | (u32(s[i + 1]) << 8) |
               (u32(s[i + 2]) << 16) | (u32(s[i + 3]) << 24);
  return sz((v * kHashMul) >> (32 - kHashLog));
}

inline bool same4(const Bytes& s, size_t a, size_t b) {
  return s[a] == s[b] && s[a + 1] == s[b + 1] && s[a + 2] == s[b + 2] &&
         s[a + 3] == s[b + 3];
}

// 시퀀스 하나. has_match 가 거짓이면 마지막(리터럴만) 시퀀스다.
inline void emit(Bytes& out, const Bytes& src, size_t from, size_t to,
                 bool has_match, size_t offset, size_t length) {
  size_t lit_len = to - from;
  size_t token_lit = std::min<size_t>(lit_len, 15);
  if (!has_match) {
    out.push_back(u8(token_lit << 4));
    if (lit_len >= 15) put_lsic(out, lit_len - 15);
    out.insert(out.end(), src.begin() + ix(from), src.begin() + ix(to));
    return;
  }
  size_t ml_code = length - kMinMatch;
  size_t token_ml = std::min<size_t>(ml_code, 15);
  out.push_back(u8((token_lit << 4) | token_ml));
  if (lit_len >= 15) put_lsic(out, lit_len - 15);
  out.insert(out.end(), src.begin() + ix(from), src.begin() + ix(to));
  out.push_back(u8(offset & 0xFF));
  out.push_back(u8(offset >> 8));
  if (ml_code >= 15) put_lsic(out, ml_code - 15);
}

inline Bytes compress_block(const Bytes& src) {
  size_t n = src.size();
  Bytes out;
  if (n < kMfLimit + 1) {
    emit(out, src, 0, n, false, 0, 0);
    return out;
  }
  std::vector<int64_t> table(kHashSize, -1);
  size_t ip = 0, anchor = 0;
  while (ip <= n - kMfLimit) {
    size_t h = hash4(src, ip);
    int64_t ref = table[h];
    table[h] = i32(0) + static_cast<int64_t>(ip);
    if (ref >= 0 && ip - sz(ref) <= kMaxOffset &&
        same4(src, sz(ref), ip)) {
      size_t ml = kMinMatch;
      size_t limit = n - kLastLiterals;
      while (ip + ml < limit && src[sz(ref) + ml] == src[ip + ml]) ++ml;
      emit(out, src, anchor, ip, true, ip - sz(ref), ml);
      ip += ml;
      anchor = ip;
    } else {
      ++ip;
    }
  }
  emit(out, src, anchor, n, false, 0, 0);
  return out;
}

inline Bytes decompress_block(const Bytes& block, bool check,
                              size_t want) {
  Bytes out;
  size_t pos = 0, n = block.size();
  while (pos < n) {
    uint8_t token = block[pos++];
    size_t lit_len = token >> 4;
    if (lit_len == 15) lit_len += get_lsic(block, pos);
    if (pos + lit_len > n) fail("리터럴이 잘렸다");
    out.insert(out.end(), block.begin() + ix(pos),
               block.begin() + ix(pos + lit_len));
    pos += lit_len;
    if (pos == n) break;          // 마지막 시퀀스는 리터럴뿐이다
    if (pos + 2 > n) fail("거리가 잘렸다");
    size_t offset = sz(block[pos]) | (sz(block[pos + 1]) << 8);
    pos += 2;
    size_t length = token & 15;
    if (length == 15) length += get_lsic(block, pos);
    length += kMinMatch;
    if (offset == 0) fail("거리 0 은 없다");
    if (offset > out.size()) fail("거리가 지금까지 낸 것보다 멀다");
    size_t start = out.size() - offset;
    // 한 바이트씩 앞으로. 거리 1 짜리 긴 일치가 여기 기댄다.
    for (size_t j = 0; j < length; ++j) out.push_back(out[start + j]);
  }
  if (check && out.size() != want) fail("푼 길이가 헤더와 다르다");
  return out;
}

inline Bytes encode(const Bytes& src) {
  if (src.empty()) return varint::put(0);
  Bytes out = varint::put(src.size());
  Bytes block = compress_block(src);
  out.insert(out.end(), block.begin(), block.end());
  return out;
}

inline Bytes decode(const Bytes& src) {
  size_t pos = 0;
  size_t n = varint::get_length(src, pos);
  if (n == 0) {
    if (pos != src.size()) fail("빈 입력인데 뒤에 바이트가 있다");
    return Bytes();
  }
  Bytes block(src.begin() + ix(pos), src.end());
  return decompress_block(block, true, n);
}

// 진짜 lz4 명령이 쓰는 프레임을 푼다 (§14.6). 쓰지는 않는다.
// 내용 검사합(xxHash)은 건너뛴다 — 이유는 명세에 적어 뒀다.
inline Bytes frame_decode(const Bytes& src) {
  if (src.size() < 7 || src[0] != 0x04 || src[1] != 0x22 ||
      src[2] != 0x4D || src[3] != 0x18) {
    fail("lz4 프레임 매직이 아니다");
  }
  uint8_t flg = src[4];
  if ((flg >> 6) != 1) fail("모르는 프레임 판");
  bool block_checksum = (flg & 0x10) != 0;
  bool content_size = (flg & 0x08) != 0;
  bool content_checksum = (flg & 0x04) != 0;
  bool dict_id = (flg & 0x01) != 0;
  size_t pos = 6;
  if (content_size) pos += 8;
  if (dict_id) pos += 4;
  pos += 1;                       // 머리 검사 바이트(HC)
  Bytes out;
  for (;;) {
    if (pos + 4 > src.size()) fail("블록 크기가 잘렸다");
    uint32_t size = u32(src[pos]) | (u32(src[pos + 1]) << 8) |
                    (u32(src[pos + 2]) << 16) |
                    (u32(src[pos + 3]) << 24);
    pos += 4;
    if (size == 0) break;
    bool stored = (size & 0x80000000u) != 0;
    size &= 0x7FFFFFFFu;
    if (pos + size > src.size()) fail("블록이 잘렸다");
    Bytes chunk(src.begin() + ix(pos), src.begin() + ix(pos + size));
    pos += size;
    if (block_checksum) pos += 4;
    if (stored) {
      out.insert(out.end(), chunk.begin(), chunk.end());
    } else {
      Bytes part = decompress_block(chunk, false, 0);
      out.insert(out.end(), part.begin(), part.end());
    }
  }
  if (content_checksum) pos += 4;
  return out;
}

}  // namespace lz4block
}  // namespace compresslib

#endif
