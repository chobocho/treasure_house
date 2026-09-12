// -*- coding: utf-8 -*-
// 문맥 혼합 — SPEC §18.
//
// 여기까지의 코덱은 모델을 **하나** 골랐다. 문맥 혼합은 고르지 않는다
// — 여러 모델에게 묻고 **의견을 섞으며** 누구를 믿을지 배운다.
//
// 섞는 자리가 요점이다. 확률을 그냥 평균 내면 0.01 과 0.99 가 0.5 가
// 되어 두 모델의 확신이 사라진다. **로지스틱 영역** 에서 더해야 한다.
#ifndef COMPRESSLIB_CM_H
#define COMPRESSLIB_CM_H

#include <array>

#include "common.h"
#include "rangecoder.h"
#include "varint.h"

namespace compresslib {
namespace cm {

constexpr int kTableBits = 20;
constexpr size_t kTableSize = size_t{1} << kTableBits;
constexpr int kNumModels = 5;
constexpr int kProbOne = 4096;
constexpr int kProbHalf = kProbOne / 2;
// 셈이 쌓일수록 천천히 움직인다. 처음 보는 문맥은 빨리 배우고 오래 본
// 문맥은 흔들리지 않아야 한다 — 고정 비율 하나로는 둘 다 못 한다.
constexpr std::array<int, 16> kCounterRates = {1, 1, 2, 2, 3, 3, 4, 4,
                                               4, 5, 5, 5, 5, 5, 5, 5};
constexpr int kCounterLimit = 15;
constexpr int kMixerShift = 16;
constexpr int kMixerInit = 1 << 14;
// 믹서 갱신의 시프트. lpaq 과 같은 16이다. 10 으로 두면 가중치가 한
// 걸음에 5만씩 튀어 모델이 수렴하지 못한다.
constexpr int kMixerUpdateShift = 16;
constexpr int kMixerLearn = 16;
constexpr int kMixerClamp = 1 << 20;
constexpr int kApmRate = 7;
constexpr size_t kApm1Contexts = 256;
constexpr size_t kApm2Contexts = size_t{1} << 16;
constexpr uint32_t kHashA = 0x9E3779B1u;
constexpr uint32_t kHashB = 0x85EBCA6Bu;

// SQUASH-TABLE-BEGIN — gen_tables.py 가 다섯을 대조한다 (§18.6)
constexpr std::array<int, 33> kSquashTable = {
    1, 2, 3, 6, 10, 16, 27, 45, 73, 120, 194, 310, 488, 747, 1101,
    1546, 2047, 2549, 2994, 3348, 3607, 3785, 3901, 3975, 4024,
    4050, 4068, 4079, 4085, 4089, 4092, 4093, 4094};
// SQUASH-TABLE-END

// 로지스틱: -2047..2047 → 0..4095. 표 사이를 직선으로 잇는다.
inline int squash(int d) {
  if (d > 2047) return 4095;
  if (d < -2047) return 0;
  int w = d & 127;
  int i = (d >> 7) + 16;
  return (kSquashTable[sz(i)] * (128 - w) +
          kSquashTable[sz(i + 1)] * w + 64) >> 7;
}

// squash 의 역. 표를 뒤집어 만든다 — 따로 적을 값이 아니다.
inline const std::vector<int16_t>& stretch_table() {
  static const std::vector<int16_t> t = [] {
    std::vector<int16_t> table(kProbOne, 0);
    int pi = 0;
    for (int x = -2047; x <= 2047; ++x) {
      int v = squash(x);
      for (int p = pi; p <= v; ++p) {
        table[sz(p)] = static_cast<int16_t>(x);
      }
      pi = v + 1;
    }
    for (int p = pi; p < kProbOne; ++p) table[sz(p)] = 2047;
    return table;
  }();
  return t;
}

inline int stretch(int p) { return stretch_table()[sz(p)]; }

inline size_t hash_ctx(uint32_t ctx, uint32_t c0) {
  uint32_t h = (ctx * kHashA) ^ (c0 * kHashB);
  return sz(h >> (32 - kTableBits));
}

// 적응 확률 지도 — 믹서의 답을 문맥에 맞춰 한 번 더 고친다 (§18.5).
class Apm {
 public:
  explicit Apm(size_t contexts) : t_(contexts * 33) {
    for (size_t i = 0; i < t_.size(); ++i) {
      t_[i] = squash((i32(i % 33) - 16) * 128) * 16;
    }
  }
  int pp(int pr, size_t cx) {
    // 곱수는 32 다. 표가 33칸이라 0..4095 를 0..32 로 펴야 끝까지
    // 쓴다. lpaq1 의 23 이면 위쪽 아홉 칸이 죽어 확률이 잘린다.
    int s = (stretch(pr) + 2048) * 32;
    int wt = s & 0xFFF;
    size_t j = cx * 33 + sz(s >> 12);
    index_ = j + sz(wt >> 11);
    return (t_[j] * (4096 - wt) + t_[j + 1] * wt) >> 16;
  }
  void update(int bit) {
    int g = (bit << 16) + (bit << kApmRate) - bit - bit;
    t_[index_] += (g - t_[index_]) >> kApmRate;
  }

 private:
  std::vector<int32_t> t_;
  size_t index_ = 0;
};

// 문맥 모델 다섯 + 믹서 + APM 둘. 부호기와 복호기가 똑같이 쓴다.
class Model {
 public:
  Model()
      : order0_(256, kProbHalf),
        order0_n_(256, 0),
        apm1_(kApm1Contexts),
        apm2_(kApm2Contexts) {
    for (int k = 0; k < 4; ++k) {
      tables_[sz(k)].assign(kTableSize, kProbHalf);
      counts_[sz(k)].assign(kTableSize, 0);
    }
    weights_.assign(256 * kNumModels, kMixerInit);
  }

  int predict() {
    uint32_t c0 = c0_;
    uint32_t h = history_;
    slots_[0] = sz(c0 & 0xFF);
    for (int k = 0; k < 4; ++k) {
      uint32_t mask =
          (k == 3) ? 0xFFFFFFFFu : ((1u << (8 * (k + 1))) - 1);
      uint32_t ctx = h & mask;
      slots_[sz(k) + 1] = hash_ctx(ctx + u32(k + 1) * 0x01000193u, c0);
    }
    int probs[kNumModels];
    probs[0] = order0_[slots_[0]];
    for (int k = 0; k < 4; ++k) {
      probs[k + 1] = tables_[sz(k)][slots_[sz(k) + 1]];
    }
    size_t wbase = sz(c0 & 0xFF) * kNumModels;
    int64_t dot = 0;
    for (int i = 0; i < kNumModels; ++i) {
      st_[sz(i)] = stretch(probs[i]);
      dot += int64_t(weights_[wbase + sz(i)]) * st_[sz(i)];
    }
    dot >>= kMixerShift;
    if (dot > 2047) dot = 2047;
    if (dot < -2047) dot = -2047;
    p_mix_ = squash(i32(dot));
    int p = (p_mix_ + 3 * apm1_.pp(p_mix_, sz(c0 & 0xFF))) >> 2;
    size_t cx2 = sz(((c0 & 0xFF) << 8) | (h & 0xFF));
    p = (p + 3 * apm2_.pp(p, cx2)) >> 2;
    if (p < 1) p = 1;
    if (p > 4094) p = 4094;
    return p;
  }

  void update(int bit) {
    int target = bit << 12;
    size_t i0 = slots_[0];
    int r0 = kCounterRates[sz(order0_n_[i0])];
    order0_[i0] = static_cast<uint16_t>(
        order0_[i0] + ((target - i32(order0_[i0])) >> r0));
    if (order0_n_[i0] < kCounterLimit) order0_n_[i0] += 1;
    for (int k = 0; k < 4; ++k) {
      size_t i = slots_[sz(k) + 1];
      auto& t = tables_[sz(k)];
      auto& c = counts_[sz(k)];
      t[i] = static_cast<uint16_t>(
          t[i] + ((target - i32(t[i])) >> kCounterRates[sz(c[i])]));
      if (c[i] < kCounterLimit) c[i] += 1;
    }
    int err = (target - p_mix_) * kMixerLearn;
    size_t wbase = sz(c0_ & 0xFF) * kNumModels;
    for (int i = 0; i < kNumModels; ++i) {
      int64_t v = weights_[wbase + sz(i)] +
                  ((int64_t(st_[sz(i)]) * err) >> kMixerUpdateShift);
      if (v > kMixerClamp) v = kMixerClamp;
      if (v < -kMixerClamp) v = -kMixerClamp;
      weights_[wbase + sz(i)] = i32(v);
    }
    apm1_.update(bit);
    apm2_.update(bit);
    c0_ = (c0_ << 1) | u32(bit);
    if (c0_ >= 256) {
      history_ = (history_ << 8) | (c0_ & 0xFF);
      c0_ = 1;
    }
  }

 private:
  std::vector<uint16_t> order0_;
  std::vector<uint8_t> order0_n_;
  std::array<std::vector<uint16_t>, 4> tables_;
  std::array<std::vector<uint8_t>, 4> counts_;
  std::vector<int32_t> weights_;
  Apm apm1_, apm2_;
  uint32_t history_ = 0;
  uint32_t c0_ = 1;
  std::array<size_t, kNumModels> slots_{};
  std::array<int, kNumModels> st_{};
  int p_mix_ = kProbHalf;
};

inline Bytes encode(const Bytes& src) {
  if (src.empty()) return varint::put(0);
  rangecoder::Encoder enc;
  Model model;
  for (uint8_t b : src) {
    for (int i = 7; i >= 0; --i) {
      int bit = (b >> i) & 1;
      int p = model.predict();
      // 코더는 P(0) 을 받는다. 모델은 P(1) 을 내므로 뒤집는다.
      enc.encode_bit_p0(u32(kProbOne - p), bit);
      model.update(bit);
    }
  }
  enc.flush();
  Bytes out = varint::put(src.size());
  out.insert(out.end(), enc.bytes().begin(), enc.bytes().end());
  return out;
}

inline Bytes decode(const Bytes& src) {
  size_t pos = 0;
  size_t n = varint::get_length(src, pos);
  if (n == 0) {
    if (pos != src.size()) fail("빈 입력인데 뒤에 바이트가 있다");
    return Bytes();
  }
  rangecoder::Decoder dec(src, pos);
  Model model;
  Bytes out;
  out.reserve(n);
  for (size_t k = 0; k < n; ++k) {
    int byte = 0;
    for (int i = 0; i < 8; ++i) {
      int p = model.predict();
      int bit = dec.decode_bit_p0(u32(kProbOne - p));
      model.update(bit);
      byte = (byte << 1) | bit;
    }
    out.push_back(u8(byte));
  }
  return out;
}

}  // namespace cm
}  // namespace compresslib

#endif
