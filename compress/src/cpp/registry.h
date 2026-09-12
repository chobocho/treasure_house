// -*- coding: utf-8 -*-
// 알고리즘 이름 → 부호기·복호기. 이름이 곧 golden/ 의 디렉터리다.
// 다섯 언어가 같은 이름·같은 순서를 갖는다.
#ifndef COMPRESSLIB_REGISTRY_H
#define COMPRESSLIB_REGISTRY_H

#include <functional>
#include <string>

#include "ans.h"
#include "bwt.h"
#include "bzip2dec.h"
#include "common.h"
#include "deflate.h"
#include "huffman.h"
#include "intcode.h"
#include "lz4block.h"
#include "lzmadec.h"
#include "lzss.h"
#include "lzw.h"
#include "mtf.h"
#include "ppm.h"
#include "rangecoder.h"
#include "rle.h"

namespace compresslib {
namespace registry {

using Codec = Bytes (*)(const Bytes&);

struct Entry {
  const char* name;
  Codec encode;       // 복호기만 있는 모듈에서는 nullptr
  Codec decode;
};

// 순서가 곧 배우는 순서다 (PLAN.md §3 Tier 1).
inline const std::vector<Entry>& entries() {
  static const std::vector<Entry> v = {
      {"bitio", bitio::encode, bitio::decode},
      {"intcode", intcode::encode, intcode::decode},
      {"rle", rle::encode, rle::decode},
      {"mtf", mtf::encode, mtf::decode},
      {"huffman", huffman::encode, huffman::decode},
      {"lzss", lzss::encode, lzss::decode},
      {"lzw", lzw::encode, lzw::decode},
      {"rangecoder", rangecoder::encode, rangecoder::decode},
      {"bwt", bwt::encode, bwt::decode},
      {"deflate", deflate::encode, deflate::decode},
      {"ans", ans::encode, ans::decode},
      {"lz4block", lz4block::encode, lz4block::decode},
      {"ppm", ppm::encode, ppm::decode},
      // 복호기만 있는 모듈 (PLAN.md §0.4)
      {"bzip2dec", nullptr, bzip2dec::decode},
      {"lzmadec", nullptr, lzmadec::decode},
  };
  return v;
}

inline const Entry* find(const std::string& name) {
  for (const Entry& e : entries())
    if (name == e.name) return &e;
  return nullptr;
}

}  // namespace registry
}  // namespace compresslib

#endif
