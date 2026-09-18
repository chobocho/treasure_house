// SHA-1 (FIPS 180-4, SPEC.md §2) — 표준 라이브러리에 없으니 손으로.
// 64바이트 블록마다 80라운드. 조각으로 나눠 넣어도 같은 결과가 나오게
// 덜 찬 블록은 buf_ 에 모아 둔다. O(n) 시간, O(1) 추가 공간.
#include "mygit.hpp"

namespace mygit {
namespace {
uint32_t rol(uint32_t x, int n) {
    return x << n | x >> (32 - n);
}

void compress(uint32_t h[5], const unsigned char* p) {
    uint32_t w[80];
    for (int t = 0; t < 16; ++t)
        w[t] = uint32_t(p[4 * t]) << 24 | uint32_t(p[4 * t + 1]) << 16 |
               uint32_t(p[4 * t + 2]) << 8 | p[4 * t + 3];
    for (int t = 16; t < 80; ++t)
        w[t] = rol(w[t - 3] ^ w[t - 8] ^ w[t - 14] ^ w[t - 16], 1);
    uint32_t a = h[0], b = h[1], c = h[2], d = h[3], e = h[4];
    for (int t = 0; t < 80; ++t) {
        uint32_t f, k;
        if (t < 20)
            f = (b & c) | (~b & d), k = 0x5a827999;
        else if (t < 40)
            f = b ^ c ^ d, k = 0x6ed9eba1;
        else if (t < 60)
            f = (b & c) | (b & d) | (c & d), k = 0x8f1bbcdc;
        else
            f = b ^ c ^ d, k = 0xca62c1d6;
        uint32_t tmp = rol(a, 5) + f + e + k + w[t];
        e = d, d = c, c = rol(b, 30), b = a, a = tmp;
    }
    h[0] += a, h[1] += b, h[2] += c, h[3] += d, h[4] += e;
}
}  // namespace

Sha1::Sha1()
    : h_{0x67452301, 0xefcdab89, 0x98badcfe, 0x10325476, 0xc3d2e1f0} {}

Sha1& Sha1::update(std::string_view data) {
    n_ += data.size();
    buf_.append(data);
    size_t k = 0;
    for (; k + 64 <= buf_.size(); k += 64)
        compress(h_, reinterpret_cast<const unsigned char*>(&buf_[k]));
    buf_.erase(0, k);
    return *this;
}

// digest 는 사본에 덧붙임(0x80, 0 들, 비트 길이 8바이트)을 넣어 끝낸다
// — 그래서 불러도 상태가 바뀌지 않는다.
std::array<uint8_t, 20> Sha1::digest() const {
    Sha1 c = *this;
    uint64_t bits = n_ * 8;
    std::string pad(1, '\x80');
    pad.append((55 - n_ % 64 + 64) % 64, '\0');
    for (int i = 7; i >= 0; --i) pad += char(bits >> (8 * i));
    c.update(pad);
    std::array<uint8_t, 20> out;
    for (int i = 0; i < 20; ++i)
        out[i] = uint8_t(c.h_[i / 4] >> (24 - 8 * (i % 4)));
    return out;
}

std::string sha1_raw(std::string_view data) {
    auto d = Sha1().update(data).digest();
    return std::string(d.begin(), d.end());
}

std::string sha1_hex(std::string_view data) {
    return to_hex(sha1_raw(data));
}

std::string to_hex(std::string_view raw) {
    static const char* digits = "0123456789abcdef";
    std::string out;
    for (unsigned char c : raw)
        out += digits[c >> 4], out += digits[c & 15];
    return out;
}

std::string from_hex(std::string_view hex) {
    auto val = [](char c) { return c <= '9' ? c - '0' : c - 'a' + 10; };
    std::string out;
    for (size_t i = 0; i + 1 < hex.size(); i += 2)
        out += char(val(hex[i]) << 4 | val(hex[i + 1]));
    return out;
}
}  // namespace mygit
