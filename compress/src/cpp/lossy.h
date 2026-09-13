// -*- coding: utf-8 -*-
// 손실 압축 — SPEC §19.
//
// 여기까지는 한 비트도 안 버렸다. 이 모듈은 **일부러 버린다.** 버리는
// 자리는 딱 하나, 양자화다 — DCT 도 PNG 필터도 그 자체로는 안 버린다.
//
// **레지스트리에 오르는 코덱은 PNG 쪽** 이다. 왕복하는 것이 그것뿐이다.
// 손실 코덱에 골든 벡터를 붙이면 부호기만 못 박는 꼴이다.
#ifndef COMPRESSLIB_LOSSY_H
#define COMPRESSLIB_LOSSY_H

#include <algorithm>
#include <array>

#include "common.h"
#include "deflate.h"
#include "huffman.h"
#include "varint.h"

namespace compresslib {
namespace lossy {

constexpr int kDctScale = 13;
constexpr int kDctRound = 1 << (kDctScale - 1);
constexpr int kBlock = 8;
constexpr size_t kPngWidth = 256;   // 골든 코덱이 쓰는 행 폭 (§19.5)
constexpr size_t kPngBpp = 1;
constexpr int kEob = 255;

// DCT-TABLE-BEGIN — gen_tables.py 가 다섯 언어를 대조한다 (§19.2)
constexpr std::array<int, 64> kDct = {
    2896, 2896, 2896, 2896, 2896, 2896, 2896, 2896,
    4017, 3406, 2276, 799, -799, -2276, -3406, -4017,
    3784, 1567, -1567, -3784, -3784, -1567, 1567, 3784,
    3406, -799, -4017, -2276, 2276, 4017, 799, -3406,
    2896, -2896, -2896, 2896, 2896, -2896, -2896, 2896,
    2276, -4017, 799, 3406, -3406, -799, 4017, -2276,
    1567, -3784, 3784, -1567, -1567, 3784, -3784, 1567,
    799, -2276, 3406, -4017, 4017, -3406, 2276, -799};
// DCT-TABLE-END

// JPEGQ-TABLE-BEGIN — gen_tables.py 가 다섯 언어를 대조한다 (§19.4)
constexpr std::array<int, 64> kJpegQuant = {
    16, 11, 10, 16, 24, 40, 51, 61,
    12, 12, 14, 19, 26, 58, 60, 55,
    14, 13, 16, 24, 40, 57, 69, 56,
    14, 17, 22, 29, 51, 87, 80, 62,
    18, 22, 37, 56, 68, 109, 103, 77,
    24, 35, 55, 64, 81, 104, 113, 92,
    49, 64, 78, 87, 103, 121, 120, 101,
    72, 92, 95, 98, 112, 100, 103, 99};
// JPEGQ-TABLE-END

// ADPCMSTEP-TABLE-BEGIN — gen_tables.py 가 대조한다 (§19.6)
constexpr std::array<int, 89> kAdpcmStep = {
    7, 8, 9, 10, 11, 12, 13, 14, 16, 17, 19, 21, 23, 25, 28, 31,
    34, 37, 41, 45, 50, 55, 60, 66, 73, 80, 88, 97, 107, 118, 130,
    143, 157, 173, 190, 209, 230, 253, 279, 307, 337, 371, 408, 449,
    494, 544, 598, 658, 724, 796, 876, 963, 1060, 1166, 1282, 1411,
    1552, 1707, 1878, 2066, 2272, 2499, 2749, 3024, 3327, 3660, 4026,
    4428, 4871, 5358, 5894, 6484, 7132, 7845, 8630, 9493, 10442, 11487,
    12635, 13899, 15289, 16818, 18500, 20350, 22385, 24623, 27086,
    29794, 32767};
// ADPCMSTEP-TABLE-END

// ADPCMINDEX-TABLE-BEGIN — gen_tables.py 가 대조한다 (§19.6)
constexpr std::array<int, 16> kAdpcmIndex = {
    -1, -1, -1, -1, 2, 4, 6, 8,
    -1, -1, -1, -1, 2, 4, 6, 8};
// ADPCMINDEX-TABLE-END

// 8×8 을 대각선으로 훑는 순서. 표가 아니라 규칙이라 여기서 만든다.
inline const std::array<int, 64>& zigzag() {
  static const std::array<int, 64> z = [] {
    std::array<int, 64> out{};
    int k = 0;
    for (int s = 0; s < 15; ++s) {
      std::vector<std::pair<int, int>> cells;
      for (int x = 0; x < 8; ++x) {
        int y = s - x;
        if (y >= 0 && y < 8) cells.emplace_back(x, y);
      }
      if (s % 2 == 1) std::reverse(cells.begin(), cells.end());
      for (auto& c : cells) out[sz(k++)] = c.second * 8 + c.first;
    }
    return out;
  }();
  return z;
}

// 버리는 곳은 여기 하나뿐이다 (§19.3).
inline int quantise(int v, int q, bool dead_zone) {
  if (dead_zone) return v < 0 ? -((-v) / q) : v / q;
  if (v < 0) return -((-v * 2 + q) / (2 * q));
  return (v * 2 + q) / (2 * q);
}

inline int dequantise(int v, int q) { return v * q; }

// 8×8 정수 DCT. 1차원 변환 두 번, 각각 반올림 (§19.2).
inline std::array<int, 64> fdct8(const std::array<int, 64>& block) {
  std::array<int, 64> tmp{}, out{};
  for (int u = 0; u < 8; ++u) {
    for (int y = 0; y < 8; ++y) {
      int s = 0;
      for (int x = 0; x < 8; ++x)
        s += kDct[sz(u * 8 + x)] * block[sz(x * 8 + y)];
      tmp[sz(u * 8 + y)] = (s + kDctRound) >> kDctScale;
    }
  }
  for (int u = 0; u < 8; ++u) {
    for (int v = 0; v < 8; ++v) {
      int s = 0;
      for (int y = 0; y < 8; ++y)
        s += kDct[sz(v * 8 + y)] * tmp[sz(u * 8 + y)];
      out[sz(u * 8 + v)] = (s + kDctRound) >> kDctScale;
    }
  }
  return out;
}

inline std::array<int, 64> idct8(const std::array<int, 64>& coef) {
  std::array<int, 64> tmp{}, out{};
  for (int x = 0; x < 8; ++x) {
    for (int v = 0; v < 8; ++v) {
      int s = 0;
      for (int u = 0; u < 8; ++u)
        s += kDct[sz(u * 8 + x)] * coef[sz(u * 8 + v)];
      tmp[sz(x * 8 + v)] = (s + kDctRound) >> kDctScale;
    }
  }
  for (int x = 0; x < 8; ++x) {
    for (int y = 0; y < 8; ++y) {
      int s = 0;
      for (int v = 0; v < 8; ++v)
        s += kDct[sz(v * 8 + y)] * tmp[sz(x * 8 + v)];
      out[sz(x * 8 + y)] = (s + kDctRound) >> kDctScale;
    }
  }
  return out;
}

// 품질 1~100 로 JPEG 표준표를 늘리고 줄인다 (§19.4).
inline std::array<int, 64> quant_table(int quality) {
  if (quality < 1 || quality > 100) fail("품질은 1~100 이다");
  int scale = quality < 50 ? 5000 / quality : 200 - 2 * quality;
  std::array<int, 64> out{};
  for (int i = 0; i < 64; ++i) {
    int q = (kJpegQuant[sz(i)] * scale + 50) / 100;
    out[sz(i)] = std::max(1, std::min(255, q));
  }
  return out;
}

// --------------------------------------------------------- jpeglite
// 우리 형식이다. JPEG 이 아니다 (§19.4).
constexpr std::array<uint8_t, 3> kJpegMagic = {'J', 'L', '1'};

inline Bytes jpeglite_encode(const Bytes& pixels, size_t width,
                             size_t height, int quality) {
  if (width * height != pixels.size()) {
    fail("픽셀 수가 너비×높이와 다르다");
  }
  if (width == 0 || height == 0 || width > 0xFFFF || height > 0xFFFF) {
    fail("크기가 범위를 벗어났다");
  }
  std::array<int, 64> qt = quant_table(quality);
  const std::array<int, 64>& zz = zigzag();
  Bytes stream;
  for (size_t by = 0; by < height; by += kBlock) {
    for (size_t bx = 0; bx < width; bx += kBlock) {
      std::array<int, 64> block{};
      for (int y = 0; y < kBlock; ++y) {
        size_t sy = std::min(by + sz(y), height - 1);
        for (int x = 0; x < kBlock; ++x) {
          size_t sx = std::min(bx + sz(x), width - 1);
          block[sz(x * 8 + y)] = i32(pixels[sy * width + sx]) - 128;
        }
      }
      std::array<int, 64> coef = fdct8(block);
      int run = 0;
      for (int k = 0; k < 64; ++k) {
        int idx = zz[sz(k)];
        int v = quantise(coef[sz(idx)], qt[sz(idx)], k > 0);
        if (v == 0 && k > 0) {
          ++run;
          continue;
        }
        while (run >= kEob) {
          stream.push_back(u8(kEob - 1));
          stream.push_back(0);
          run -= kEob;
        }
        stream.push_back(u8(run));
        uint64_t z = (v >= 0) ? (u64(v) << 1) : ((u64(-v) << 1) - 1);
        varint::put(stream, z);
        run = 0;
      }
      stream.push_back(u8(kEob));
    }
  }
  Bytes out(kJpegMagic.begin(), kJpegMagic.end());
  out.push_back(u8(width & 0xFF));
  out.push_back(u8(width >> 8));
  out.push_back(u8(height & 0xFF));
  out.push_back(u8(height >> 8));
  out.push_back(u8(quality));
  Bytes body = huffman::encode(stream);
  out.insert(out.end(), body.begin(), body.end());
  return out;
}

// (픽셀, 너비, 높이). 원본과 같지 않다 — 그게 이 형식의 약속이다.
inline Bytes jpeglite_decode(const Bytes& src, size_t& width,
                             size_t& height) {
  if (src.size() < 8 || src[0] != 'J' || src[1] != 'L'
      || src[2] != '1') {
    fail("jpeglite 매직이 아니다");
  }
  width = sz(src[3]) | (sz(src[4]) << 8);
  height = sz(src[5]) | (sz(src[6]) << 8);
  int quality = src[7];
  std::array<int, 64> qt = quant_table(quality);
  const std::array<int, 64>& zz = zigzag();
  Bytes body(src.begin() + 8, src.end());
  Bytes stream = huffman::decode(body);
  size_t pos = 0;
  Bytes pixels(width * height, 0);
  for (size_t by = 0; by < height; by += kBlock) {
    for (size_t bx = 0; bx < width; bx += kBlock) {
      std::array<int, 64> coef{};
      int k = 0;
      // 끝 표시는 반드시 읽어 치운다 — 64개가 다 실린 블록에서
      // 안 먹고 나가면 다음 블록이 그 255 를 자기 EOB 로 읽는다.
      for (;;) {
        if (pos >= stream.size()) fail("계수 스트림이 잘렸다");
        int run = stream[pos++];
        if (run == kEob) break;
        k += run;
        if (k >= 64) fail("0 런이 블록을 넘는다");
        uint64_t z = varint::get(stream, pos);
        int v = (z & 1) ? -i32((z + 1) >> 1) : i32(z >> 1);
        coef[sz(zz[sz(k)])] = dequantise(v, qt[sz(zz[sz(k)])]);
        ++k;
      }
      std::array<int, 64> block = idct8(coef);
      for (int y = 0; y < kBlock; ++y) {
        size_t sy = by + sz(y);
        if (sy >= height) break;
        for (int x = 0; x < kBlock; ++x) {
          size_t sx = bx + sz(x);
          if (sx >= width) break;
          int p = block[sz(x * 8 + y)] + 128;
          pixels[sy * width + sx] = u8(std::max(0, std::min(255, p)));
        }
      }
    }
  }
  return pixels;
}

// ---------------------------------------------------------- PNG 필터
// 왼쪽·위·왼쪽위 가운데 a+b-c 에 가장 가까운 것. 동점은 a, 그다음 b.
inline int paeth(int a, int b, int c) {
  int p = a + b - c;
  int pa = std::abs(p - a), pb = std::abs(p - b), pc = std::abs(p - c);
  if (pa <= pb && pa <= pc) return a;
  if (pb <= pc) return b;
  return c;
}

inline Bytes filter_row(const Bytes& row, const Bytes& prev, int kind,
                        size_t bpp) {
  Bytes out(row.size());
  for (size_t i = 0; i < row.size(); ++i) {
    int v = row[i];
    int left = i >= bpp ? row[i - bpp] : 0;
    int up = i < prev.size() ? prev[i] : 0;
    bool near = i >= bpp && i - bpp < prev.size();
    int upleft = near ? prev[i - bpp] : 0;
    int d;
    if (kind == 0) d = v;
    else if (kind == 1) d = v - left;
    else if (kind == 2) d = v - up;
    else if (kind == 3) d = v - ((left + up) >> 1);
    else d = v - paeth(left, up, upleft);
    out[i] = u8(d);
  }
  return out;
}

inline Bytes unfilter_row(const Bytes& row, const Bytes& prev, int kind,
                          size_t bpp) {
  Bytes out(row.size());
  for (size_t i = 0; i < row.size(); ++i) {
    int d = row[i];
    int left = i >= bpp ? out[i - bpp] : 0;
    int up = i < prev.size() ? prev[i] : 0;
    bool near = i >= bpp && i - bpp < prev.size();
    int upleft = near ? prev[i - bpp] : 0;
    int v;
    if (kind == 0) v = d;
    else if (kind == 1) v = d + left;
    else if (kind == 2) v = d + up;
    else if (kind == 3) v = d + ((left + up) >> 1);
    else if (kind == 4) v = d + paeth(left, up, upleft);
    else { fail("없는 필터 종류"); }
    out[i] = u8(v);
  }
  return out;
}

// 줄마다 다섯 후보 가운데 절댓값 합이 가장 작은 것을 고른다 (§19.5).
inline Bytes png_filter(const Bytes& data, size_t width,
                        size_t bpp = kPngBpp) {
  Bytes out;
  Bytes prev;
  for (size_t off = 0; off < data.size(); off += width) {
    size_t end = std::min(off + width, data.size());
    Bytes row(data.begin() + ix(off), data.begin() + ix(end));
    int best_kind = 0;
    Bytes best_row;
    long best_score = -1;
    for (int kind = 0; kind < 5; ++kind) {
      Bytes cand = filter_row(row, prev, kind, bpp);
      long score = 0;
      for (uint8_t b : cand) score += (b < 128) ? b : (256 - b);
      if (best_score < 0 || score < best_score) {
        best_kind = kind;
        best_row = cand;
        best_score = score;
      }
    }
    out.push_back(u8(best_kind));
    out.insert(out.end(), best_row.begin(), best_row.end());
    prev = row;
  }
  return out;
}

inline Bytes png_unfilter(const Bytes& data, size_t width,
                          size_t bpp = kPngBpp) {
  Bytes out;
  Bytes prev;
  size_t pos = 0;
  while (pos < data.size()) {
    int kind = data[pos++];
    size_t n = std::min(width, data.size() - pos);
    Bytes row(data.begin() + ix(pos), data.begin() + ix(pos + n));
    Bytes decoded = unfilter_row(row, prev, kind, bpp);
    pos += n;
    out.insert(out.end(), decoded.begin(), decoded.end());
    prev = decoded;
  }
  return out;
}

// 골든 코덱 — 이 모듈에서 유일하게 왕복한다 (§19.1).
inline Bytes encode(const Bytes& src) {
  if (src.empty()) return varint::put(0);
  Bytes out = varint::put(src.size());
  Bytes body = deflate::encode(png_filter(src, kPngWidth));
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
  Bytes body(src.begin() + ix(pos), src.end());
  Bytes out = png_unfilter(deflate::decode(body), kPngWidth);
  if (out.size() != n) fail("푼 길이가 헤더와 다르다");
  return out;
}

// ----------------------------------------------------------- IMA ADPCM
// 예측기를 안 보내는 것이 요점이다 — 복호기의 표류가 곧 부호기의
// 표류다.
inline Bytes adpcm_encode(const std::vector<int>& samples) {
  Bytes out;
  int predictor = 0, index = 0, half = -1;
  for (int s : samples) {
    int step = kAdpcmStep[sz(index)];
    int diff = s - predictor;
    int code = 0;
    if (diff < 0) {
      code = 8;
      diff = -diff;
    }
    int mag = std::min(7, (diff * 4) / step);
    code |= mag;
    int delta = step >> 3;
    if (mag & 4) delta += step;
    if (mag & 2) delta += step >> 1;
    if (mag & 1) delta += step >> 2;
    predictor += (code & 8) ? -delta : delta;
    predictor = std::max(-32768, std::min(32767, predictor));
    int step_delta = kAdpcmIndex[sz(code & 7)];
    index = std::max(0, std::min(88, index + step_delta));
    if (half < 0) {
      half = code;
    } else {
      out.push_back(u8((half << 4) | code));
      half = -1;
    }
  }
  if (half >= 0) out.push_back(u8(half << 4));
  return out;
}

inline std::vector<int> adpcm_decode(const Bytes& data, size_t count) {
  std::vector<int> out;
  out.reserve(count);
  int predictor = 0, index = 0;
  for (size_t i = 0; i < count; ++i) {
    if ((i >> 1) >= data.size()) fail("ADPCM 스트림이 잘렸다");
    int byte = data[i >> 1];
    int code = ((i & 1) == 0) ? (byte >> 4) : (byte & 0x0F);
    int step = kAdpcmStep[sz(index)];
    int mag = code & 7;
    int delta = step >> 3;
    if (mag & 4) delta += step;
    if (mag & 2) delta += step >> 1;
    if (mag & 1) delta += step >> 2;
    predictor += (code & 8) ? -delta : delta;
    predictor = std::max(-32768, std::min(32767, predictor));
    int step_delta = kAdpcmIndex[sz(code & 7)];
    index = std::max(0, std::min(88, index + step_delta));
    out.push_back(predictor);
  }
  return out;
}

}  // namespace lossy
}  // namespace compresslib

#endif
