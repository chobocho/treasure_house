// -*- coding: utf-8 -*- zlib 과 gzip 컨테이너 — SPEC §10.8. gzip 머리의
// MTIME 은 0 이다. 진짜 gzip 은 수정 시각을 적어 같은 입력에 같은
// 바이트가 안 나온다 — 우리 캡처는 재현되어야 한다.
#ifndef COMPRESSLIB_CONTAINERS_H
#define COMPRESSLIB_CONTAINERS_H

#include "checksums.h"
#include "common.h"
#include "deflate.h"
#include "inflate.h"

namespace compresslib {
namespace containers {

constexpr uint8_t kZlibCmf = 0x78;
constexpr uint8_t kZlibFlg = 0x9C;
constexpr uint8_t kGzipDeflate = 8;
constexpr uint8_t kGzipOsUnknown = 255;

inline Bytes zlib_compress(const Bytes& src) {
  Bytes out{kZlibCmf, kZlibFlg};
  Bytes raw = deflate::deflate_raw(src);
  out.insert(out.end(), raw.begin(), raw.end());
  uint32_t a = checksums::adler32(src);
  for (int i = 3; i >= 0; --i)
    out.push_back(u8((a >> (8 * i)) & 0xFF));
  return out;
}

inline Bytes zlib_decompress(const Bytes& src) {
  if (src.size() < 6) fail("zlib 스트림이 너무 짧다");
  uint32_t cmf = src[0], flg = src[1];
  if ((cmf & 0x0F) != 8) fail("zlib CM 이 8 이 아니다");
  if (((cmf << 8) | flg) % 31)
    fail("zlib 머리의 검사식이 31 로 안 나눠진다");
  if (flg & 0x20) fail("미리 정한 사전(FDICT)은 지원하지 않는다");
  Bytes body(src.begin() + 2, src.end() - 4);
  Bytes out = inflate::inflate_raw(body);
  uint32_t want = 0;
  for (size_t i = src.size() - 4; i < src.size(); ++i)
    want = (want << 8) | src[i];
  if (checksums::adler32(out) != want) fail("Adler-32 가 다르다");
  return out;
}

inline Bytes gzip_compress(const Bytes& src) {
  Bytes out{0x1F, 0x8B, kGzipDeflate, 0, 0, 0, 0, 0, 0, kGzipOsUnknown};
  Bytes raw = deflate::deflate_raw(src);
  out.insert(out.end(), raw.begin(), raw.end());
  uint32_t c = checksums::crc32(src);
  uint32_t n = u32(src.size() & 0xFFFFFFFFu);
  for (int i = 0; i < 4; ++i)
    out.push_back(u8((c >> (8 * i)) & 0xFF));
  for (int i = 0; i < 4; ++i)
    out.push_back(u8((n >> (8 * i)) & 0xFF));
  return out;
}

inline Bytes gzip_decompress(const Bytes& src) {
  if (src.size() < 18) fail("gzip 스트림이 너무 짧다");
  if (src[0] != 0x1F || src[1] != 0x8B) fail("gzip 매직이 아니다");
  if (src[2] != kGzipDeflate) fail("gzip CM 이 8 이 아니다");
  uint8_t flg = src[3];
  size_t pos = 10;
  if (flg & 0x04) {
    size_t n = sz(src[pos]) |
               (sz(src[pos + 1]) << 8);
    pos += 2 + n;
  }
  for (uint8_t bit : {uint8_t{0x08}, uint8_t{0x10}}) {
    if (flg & bit) {
      while (pos < src.size() && src[pos]) ++pos;
      ++pos;
    }
  }
  if (flg & 0x02) pos += 2;
  if (pos + 8 >= src.size()) fail("gzip 머리가 잘렸다");
  Bytes body(src.begin() + ix(pos), src.end() - 8);
  Bytes out = inflate::inflate_raw(body);
  uint32_t crc = 0, size = 0;
  for (int i = 3; i >= 0; --i)
    crc = (crc << 8) | src[src.size() - 8 + sz(i)];
  for (int i = 3; i >= 0; --i)
    size = (size << 8) | src[src.size() - 4 + sz(i)];
  if (checksums::crc32(out) != crc) fail("CRC-32 가 다르다");
  if (u32(out.size() & 0xFFFFFFFFu) != size)
    fail("ISIZE 가 푼 길이와 다르다");
  return out;
}

}  // namespace containers
}  // namespace compresslib

#endif
