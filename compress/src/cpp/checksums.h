// -*- coding: utf-8 -*-
// Adler-32 과 CRC-32 — SPEC §10.8.
//
// 표는 다항식에서 만든다. 256칸을 소스에 적어 두는 편이 빠르지만,
// 숫자 256개를 다섯 언어에 옮겨 적으면 어딘가는 틀린다.
#ifndef COMPRESSLIB_CHECKSUMS_H
#define COMPRESSLIB_CHECKSUMS_H

#include <algorithm>
#include <array>

#include "common.h"

namespace compresslib {
namespace checksums {

constexpr uint32_t kAdlerMod = 65521;
// b 가 32비트를 넘기 전에 나눠야 하는 폭 (zlib 의 NMAX)
constexpr size_t kAdlerNmax = 5552;
constexpr uint32_t kCrcPoly = 0xEDB88320u;

inline uint32_t adler32(const Bytes& data) {
  uint32_t a = 1, b = 0;
  for (size_t i = 0; i < data.size(); i += kAdlerNmax) {
    size_t end = std::min(data.size(), i + kAdlerNmax);
    for (size_t j = i; j < end; ++j) {
      a += data[j];
      b += a;
    }
    a %= kAdlerMod;
    b %= kAdlerMod;
  }
  return (b << 16) | a;
}

inline const std::array<uint32_t, 256>& crc_table() {
  static const std::array<uint32_t, 256> table = [] {
    std::array<uint32_t, 256> t{};
    for (uint32_t i = 0; i < 256; ++i) {
      uint32_t c = i;
      for (int k = 0; k < 8; ++k)
        c = (c >> 1) ^ ((c & 1) ? kCrcPoly : 0);
      t[i] = c;
    }
    return t;
  }();
  return table;
}

inline uint32_t crc32(const Bytes& data) {
  const auto& t = crc_table();
  uint32_t c = 0xFFFFFFFFu;
  for (uint8_t byte : data) c = t[(c ^ byte) & 0xFF] ^ (c >> 8);
  return c ^ 0xFFFFFFFFu;
}

}  // namespace checksums
}  // namespace compresslib

#endif
