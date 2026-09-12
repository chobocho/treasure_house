// -*- coding: utf-8 -*-
// C++ 시험 — 평범한 assert 다. gtest 같은 바깥 라이브러리를 안 쓴다.
//
// 파이썬 쪽보다 얇다. 진짜 문지기는 파서티 검사(골든 대조 + 5×5 교차
// 복호) 이고, 여기서는 그 검사가 못 보는 것만 본다 — 예외를 던져야 할
// 자리에서 진짜 던지는가, 그리고 명세의 표가 이 언어에서도 그대로
// 나오는가.
#include <cassert>
#include <cstdio>
#include <string>

#include "../containers.h"
#include "../registry.h"

using namespace compresslib;

static int checks = 0;

#define CHECK(cond)                                          \
  do {                                                       \
    ++checks;                                                \
    if (!(cond)) {                                           \
      std::printf("실패 %s:%d  %s\n", __FILE__, __LINE__,     \
                  #cond);                                    \
      return 1;                                              \
    }                                                        \
  } while (0)

static Bytes B(std::initializer_list<int> v) {
  Bytes out;
  for (int x : v) out.push_back(u8(x));
  return out;
}

static Bytes repeat(uint8_t b, size_t n) { return Bytes(n, b); }

static Bytes pseudo(size_t n, uint32_t a, uint32_t c) {
  Bytes out;
  out.reserve(n);
  for (size_t i = 0; i < n; ++i)
    out.push_back(u8((i * a + c) & 0xFF));
  return out;
}

template <class F>
static bool throws(F f) {
  try {
    f();
  } catch (const std::exception&) {
    return true;
  }
  return false;
}

static int test_bitio() {
  bitio::MsbWriter w;
  w.write_bit(1);
  w.flush();
  CHECK(w.bytes() == B({0x80}));             // 첫 비트는 7번 비트에
  bitio::MsbWriter w2;
  w2.write_bits(0b111, 3);
  w2.flush();
  CHECK(w2.bytes() == B({0xE0}));            // 채움은 0 이다
  bitio::LsbWriter w3;
  w3.write_bits(1, 1);
  w3.write_bits(1, 2);
  w3.write_code(0, 7);
  w3.flush();
  CHECK(w3.bytes() == B({0x03, 0x00}));      // 빈 DEFLATE 스트림
  CHECK(bitio::encode(Bytes()) == B({0x00, 0x00}));
  return 0;
}

static int test_intcode() {
  CHECK(varint::put(0) == B({0x00}));
  CHECK(varint::put(300) == B({0xAC, 0x02}));
  CHECK(intcode::zigzag(0) == 0);
  CHECK(intcode::zigzag(-1) == 1);
  CHECK(intcode::zigzag(1) == 2);
  CHECK(intcode::unzigzag(3) == -2);
  for (int64_t n : {int64_t{-9223372036854775807LL - 1},
                    int64_t{9223372036854775807LL}, int64_t{0}})
    CHECK(intcode::unzigzag(intcode::zigzag(n)) == n);
  bitio::MsbWriter w;
  intcode::put_gamma(w, 4);                  // 00100
  w.flush();
  CHECK(w.bytes() == B({0x20}));
  CHECK(throws([] {
    bitio::MsbWriter x;
    intcode::put_rice(x, uint64_t{1} << 40, 0);
  }));
  return 0;
}

static int test_rle() {
  CHECK(rle::encode(B({'A', 'A', 'A'})) == B({0x03, 0xFE, 'A'}));
  CHECK(rle::encode(B({'A', 'B'})) == B({0x02, 0x01, 'A', 'B'}));
  CHECK(rle::encode(repeat('A', 128)) == B({0x80, 0x01, 0x81, 'A'}));
  CHECK(throws([] { rle::decode(B({0x03, 0x80, 'A', 'A', 'A'})); }));
  std::vector<int> zeros(3, 0);
  std::vector<int> want{0, 0};
  CHECK(rle::zero_run_encode(zeros) == want);
  CHECK(rle::zero_run_decode(rle::zero_run_encode(zeros)) == zeros);
  return 0;
}

static int test_mtf() {
  CHECK(mtf::transform(B({'A', 'A', 'A', 'A'})) == B({'A', 0, 0, 0}));
  // 옮기는 것이지 바꿔치는 것이 아니다 — 바꿔치기면 마지막이 0 이 된다
  CHECK(mtf::transform(B({'C', 'B', 'A', 'B'})) ==
        B({'C', 'C', 'C', 1}));
  return 0;
}

static int test_huffman() {
  std::vector<uint64_t> f(256, 0);
  f[0] = 5;
  f[1] = 2;
  f[2] = 1;
  std::vector<int> lens = huffman::code_lengths(f);
  CHECK(lens[0] == 1 && lens[1] == 2 && lens[2] == 2);
  std::vector<uint64_t> g(256, 0);
  for (int i = 0; i < 7; ++i) g[sz(i)] = 1;
  std::vector<int> l7 = huffman::code_lengths(g);
  CHECK(l7[0] == 3 && l7[5] == 3 && l7[6] == 2);
  // RFC 1951 §3.2.2 의 예
  std::vector<int> rfc(256, 0);
  const int want[8] = {3, 3, 3, 3, 3, 2, 4, 4};
  for (int i = 0; i < 8; ++i) rfc[sz(i)] = want[i];
  std::vector<int> codes = huffman::canonical_codes(rfc);
  CHECK(codes[0] == 0b010 && codes[5] == 0b00 && codes[7] == 0b1111);
  CHECK(huffman::encode(Bytes()) == B({0x00}));
  return 0;
}

static int test_lzss() {
  CHECK(lzss::encode(B({'A'})) == B({0x01, 0x00, 'A'}));
  CHECK(lzss::encode(B({'A', 'A', 'A', 'A'})) ==
        B({0x04, 0x40, 'A', 0x00, 0x00, 0x00}));
  Bytes run = repeat('A', 1000);
  CHECK(lzss::decode(lzss::encode(run)) == run);
  CHECK(throws(
      [] { lzss::decode(B({0x03, 0x80, 0x00, 0x01, 0x00})); }));
  return 0;
}

static int test_lzw() {
  CHECK(lzw::encode(Bytes()) == B({0x00}));
  CHECK(lzw::encode(B({'A'})) == B({0x01, 0x20, 0xC0, 0x40}));
  // 사전이 두 번 이상 꽉 차는 크기 — 폭 확장의 한 칸 지연을 밟는다
  Bytes big = pseudo(200000, 131, 7);
  CHECK(lzw::decode(lzw::encode(big)) == big);
  return 0;
}

static int test_rangecoder() {
  Bytes src = pseudo(1000, 37, 11);
  Bytes out = rangecoder::encode(src);
  // 헤더(varint) 다음이 코더 스트림이고, 그 첫 바이트는 늘 0 이다.
  size_t head = varint::put(src.size()).size();
  CHECK(out[head] == 0);
  CHECK(rangecoder::decode(out) == src);
  Bytes bad = out;
  bad[head] = 1;
  CHECK(throws([&] { rangecoder::decode(bad); }));
  return 0;
}

static int test_bwt() {
  Bytes banana = B({'b', 'a', 'n', 'a', 'n', 'a'});
  Bytes l;
  uint32_t primary = 0;
  bwt::transform_block(banana, l, primary);
  CHECK(l == B({'n', 'n', 'b', 'a', 'a', 'a'}));
  CHECK(primary == 3);
  CHECK(bwt::inverse_block(l, primary) == banana);
  Bytes zeros = repeat(0, 64);
  bwt::transform_block(zeros, l, primary);
  CHECK(primary == 0);              // 동점은 시작 위치 오름차순
  return 0;
}

static int test_deflate() {
  CHECK(deflate::deflate_raw(Bytes()) == B({0x03, 0x00}));
  CHECK(inflate::inflate_raw(B({0x03, 0x00})).empty());
  CHECK(throws([] { inflate::inflate_raw(B({0x07, 0x00})); }));
  CHECK(throws([] {
    inflate::inflate_raw(B({0x01, 0x01, 0x00, 0x00, 0x00, 'A'}));
  }));
  Bytes src = pseudo(50000, 37, 11);
  CHECK(inflate::inflate_raw(deflate::deflate_raw(src)) == src);
  Bytes z = containers::zlib_compress(src);
  CHECK(containers::zlib_decompress(z) == src);
  Bytes g = containers::gzip_compress(src);
  CHECK(containers::gzip_decompress(g) == src);
  Bytes gz = containers::gzip_compress(B({'h', 'i'}));
  // MTIME 이 0 이라 같은 입력에서 늘 같은 바이트가 나온다
  CHECK(gz[4] == 0 && gz[5] == 0 && gz[6] == 0 && gz[7] == 0);
  Bytes broken = gz;
  broken[broken.size() - 5] ^= 0xFF;
  CHECK(throws([&] { containers::gzip_decompress(broken); }));
  return 0;
}

static int test_round_trips() {
  std::vector<Bytes> cases = {Bytes(), B({'A'}), repeat(0, 5000),
                              pseudo(20000, 37, 11),
                              pseudo(70000, 131, 3)};
  for (const auto& e : registry::entries()) {
    for (const Bytes& src : cases) {
      Bytes out = e.encode(src);
      if (e.decode(out) != src) {
        std::printf("실패 %s 왕복 (%zu 바이트)\n", e.name, src.size());
        return 1;
      }
      ++checks;
    }
  }
  return 0;
}

int main() {
  struct {
    const char* name;
    int (*fn)();
  } tests[] = {
      {"bitio", test_bitio},           {"intcode", test_intcode},
      {"rle", test_rle},               {"mtf", test_mtf},
      {"huffman", test_huffman},       {"lzss", test_lzss},
      {"lzw", test_lzw},               {"rangecoder", test_rangecoder},
      {"bwt", test_bwt},               {"deflate", test_deflate},
      {"round-trips", test_round_trips},
  };
  for (const auto& t : tests) {
    if (t.fn() != 0) {
      std::printf("%s 에서 멈췄다\n", t.name);
      return 1;
    }
  }
  std::printf("C++ 시험 통과 — 검사 %d건\n", checks);
  return 0;
}
