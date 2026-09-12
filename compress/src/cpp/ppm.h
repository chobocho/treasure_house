// -*- coding: utf-8 -*-
// PPM — 부분 일치 예측 — SPEC §17.
//
// 앞 두 바이트로 다음 바이트를 찍는다. 틀리면 "틀렸다"(탈출) 고 말하고
// 앞 한 바이트로, 또 틀리면 맨손으로 찍는다. 탈출값은 방법 C 다
// — 문맥에서 본 서로 다른 기호의 수가 곧 탈출의 빈도다.
//
// **모든 기호가 배제된 문맥은 건너뛴다.** 탈출이 확실해 비트가 0이다.
// 이걸 잊으면 부호기만 탈출을 적어 거기서 어긋난다 — PPM 의 고전 버그.
#ifndef COMPRESSLIB_PPM_H
#define COMPRESSLIB_PPM_H

#include <algorithm>
#include <map>

#include "common.h"
#include "rangecoder.h"
#include "varint.h"

namespace compresslib {
namespace ppm {

constexpr int kMaxOrder = 2;
constexpr int kAlphabet = 256;
// 문맥의 합계가 이 값에 닿으면 모든 셈을 반으로 줄인다. 레인지 코더가
// tot < 2^16 을 요구하기도 하고, 오래된 통계를 잊는 효과도 있다.
constexpr uint32_t kMaxTotal = 8192;

// 문맥 열쇠 — 바이트 0~2개. 길이를 같이 담아 ()·(a)·(a,b) 를 구별한다.
struct Key {
  int order;
  uint8_t a, b;
  bool operator<(const Key& o) const {
    if (order != o.order) return order < o.order;
    if (a != o.a) return a < o.a;
    return b < o.b;
  }
};

using Table = std::map<int, uint32_t>;   // 기호 → 셈 (번호 오름차순)
using Model = std::map<Key, Table>;

inline std::vector<Key> context_keys(
    const std::vector<uint8_t>& history) {
  std::vector<Key> keys;
  for (int order = kMaxOrder; order >= 0; --order) {
    if (sz(order) > history.size()) continue;
    Key k{order, 0, 0};
    if (order == 1) {
      k.a = history.back();
    } else if (order == 2) {
      k.a = history[history.size() - 2];
      k.b = history.back();
    }
    keys.push_back(k);
  }
  return keys;
}

inline void update(Model& model, const Key& key, int sym) {
  Table& table = model[key];
  table[sym] += 1;
  uint32_t total = 0;
  for (const auto& kv : table) total += kv.second;
  if (total >= kMaxTotal) {
    for (auto& kv : table) {
      kv.second = std::max<uint32_t>(1, kv.second >> 1);
    }
  }
}

// 배제되지 않은 기호를 번호 오름차순으로. 누적합의 순서가 곧 이것이다.
inline std::vector<int> visible(const Table& table,
                                const std::vector<bool>& excluded) {
  std::vector<int> syms;
  for (const auto& kv : table) {
    if (!excluded[sz(kv.first)]) syms.push_back(kv.first);
  }
  return syms;
}

inline void push_history(std::vector<uint8_t>& history, uint8_t b) {
  history.push_back(b);
  if (history.size() > sz(kMaxOrder)) history.erase(history.begin());
}

inline Bytes encode(const Bytes& src) {
  if (src.empty()) return varint::put(0);
  rangecoder::Encoder enc;
  Model model;
  std::vector<uint8_t> history;
  for (uint8_t b : src) {
    std::vector<bool> excluded(kAlphabet, false);
    bool coded = false;
    for (const Key& key : context_keys(history)) {
      auto it = model.find(key);
      if (it == model.end()) continue;
      const Table& table = it->second;
      std::vector<int> syms = visible(table, excluded);
      if (syms.empty()) continue;      // 모두 배제 — 아무것도 안 적는다
      uint32_t esc = u32(syms.size());
      uint32_t tot = esc;
      for (int s : syms) tot += table.at(s);
      if (!excluded[b] && table.count(b)) {
        uint32_t cum = 0;
        for (int s : syms) {
          if (s == b) break;
          cum += table.at(s);
        }
        enc.encode_freq(cum, table.at(b), tot);
        coded = true;
        break;
      }
      enc.encode_freq(tot - esc, esc, tot);
      for (int s : syms) excluded[sz(s)] = true;
    }
    if (!coded) {
      // -1차 — 남은 기호에 균등하게 (§17.4)
      uint32_t rest = 0, index = 0;
      for (int s = 0; s < kAlphabet; ++s) {
        if (excluded[sz(s)]) continue;
        if (s < b) ++index;
        ++rest;
      }
      enc.encode_freq(index, 1, rest);
    }
    for (const Key& key : context_keys(history)) update(model, key, b);
    push_history(history, b);
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
  std::vector<uint8_t> history;
  Bytes out;
  out.reserve(n);
  for (size_t k = 0; k < n; ++k) {
    std::vector<bool> excluded(kAlphabet, false);
    int found = -1;
    for (const Key& key : context_keys(history)) {
      auto it = model.find(key);
      if (it == model.end()) continue;
      const Table& table = it->second;
      std::vector<int> syms = visible(table, excluded);
      if (syms.empty()) continue;
      uint32_t esc = u32(syms.size());
      uint32_t tot = esc;
      for (int s : syms) tot += table.at(s);
      uint32_t v = dec.decode_freq(tot);
      uint32_t cum = 0;
      int hit = -1;
      for (int s : syms) {
        if (v >= cum && v < cum + table.at(s)) {
          hit = s;
          break;
        }
        cum += table.at(s);
      }
      if (hit >= 0) {
        dec.decode_update(cum, table.at(hit), tot);
        found = hit;
        break;
      }
      dec.decode_update(tot - esc, esc, tot);
      for (int s : syms) excluded[sz(s)] = true;
    }
    if (found < 0) {
      std::vector<int> rest;
      for (int s = 0; s < kAlphabet; ++s) {
        if (!excluded[sz(s)]) rest.push_back(s);
      }
      uint32_t v = dec.decode_freq(u32(rest.size()));
      found = rest[v];
      dec.decode_update(v, 1, u32(rest.size()));
    }
    out.push_back(u8(found));
    for (const Key& key : context_keys(history)) {
      update(model, key, found);
    }
    push_history(history, u8(found));
  }
  return out;
}

}  // namespace ppm
}  // namespace compresslib

#endif
