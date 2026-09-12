// -*- coding: utf-8 -*-
// compresslib 공통 타입 — SPEC §0.
//
// 다섯 언어가 같은 바이트를 내려면 "바이트 열" 이 무엇인지부터 같아야
// 한다. C++ 쪽은 std::vector<uint8_t> 하나로 통일한다. std::string 은
// 부호 있는 char 라 값 비교에서 사고가 나고, span 은 소유권이 없어
// 되돌려 줄 수 없다.
//
// C++ 에서 파서티가 깨지는 자리는 거의 늘 **정수 승격** 이다.
// uint8_t << 24 는 int 로 승격돼 넘치고, 그건 정의되지 않은 동작이다.
// -Werror 가 일부는 잡지만 전부는 못 잡는다 (SPEC §0.5).
#ifndef COMPRESSLIB_COMMON_H
#define COMPRESSLIB_COMMON_H

#include <cstdint>
#include <stdexcept>
#include <string>
#include <vector>

namespace compresslib {

using Bytes = std::vector<uint8_t>;

// 캐스트 이름을 짧게 줄여 둔다. 덱은 이 코드를 72칸 폭으로 보여 주는데
// static_cast<uint8_t>(...) 를 그대로 쓰면 한 줄이 두세 줄로 접혀
// 읽기가 어려워진다. 뜻은 static_cast 와 똑같다 — 이름만 짧다.
template <class T> constexpr uint8_t u8(T v) {
  return static_cast<uint8_t>(v);
}
template <class T> constexpr uint16_t u16(T v) {
  return static_cast<uint16_t>(v);
}
template <class T> constexpr uint32_t u32(T v) {
  return static_cast<uint32_t>(v);
}
template <class T> constexpr uint64_t u64(T v) {
  return static_cast<uint64_t>(v);
}
template <class T> constexpr int32_t s32(T v) {
  return static_cast<int32_t>(v);
}
template <class T> constexpr size_t sz(T v) {
  return static_cast<size_t>(v);
}
template <class T> constexpr int i32(T v) {
  return static_cast<int>(v);
}
// 반복자 뺄셈용. vector 의 iterator 는 ptrdiff_t 로 더한다.
template <class T> constexpr long ix(T v) {
  return static_cast<long>(v);
}

// 손상된 입력은 예외다. 조용히 그럴듯한 바이트를 내놓는 복호기가
// 압축에서는 가장 위험하다 (SPEC §12).
[[noreturn]] inline void fail(const std::string& why) {
  throw std::runtime_error(why);
}

}  // namespace compresslib

#endif
