// deflate(저장 블록만) · Adler-32 · CRC-32 (SPEC.md §3.1).
// 이 구현은 압축하지 않는다 — 65,535바이트씩 BTYPE=00 블록에 싸기만
// 한다. git 은 객체의 이름을 푼 바이트로 정하므로 이렇게 싼 객체도
// 그대로 읽는다(golden/stored_ok.txt). O(n).
#include "mygit.hpp"

namespace mygit {
std::string compress(std::string_view data) {
    std::string out = "\x78\x01";  // deflate, 창 32K, 수준 "가장 빠름"
    size_t pos = 0;
    do {
        size_t n = std::min<size_t>(65535, data.size() - pos);
        bool last = pos + n == data.size();
        out += char(last);  // BFINAL, BTYPE=00
        for (uint32_t v : {uint32_t(n), uint32_t(n ^ 0xffff)})
            out += char(v & 0xff), out += char(v >> 8);  // 작은 쪽부터
        out.append(data.substr(pos, n));
        pos += n;
    } while (pos < data.size());
    uint32_t a = adler32(data);
    for (int k = 3; k >= 0; --k)
        out += char(a >> (8 * k));  // 큰 쪽부터
    return out;
}

// adler32 는 두 합을 65521 로 나눈 나머지. 5552바이트마다만 나누는
// 까닭은 그 안에서는 32비트가 넘치지 않기 때문이다(zlib 의 NMAX).
uint32_t adler32(std::string_view data) {
    uint32_t a = 1, b = 0;
    for (size_t pos = 0; pos < data.size();) {
        size_t end = std::min(data.size(), pos + 5552);
        for (; pos < end; ++pos) a += uint8_t(data[pos]), b += a;
        a %= 65521, b %= 65521;
    }
    return b << 16 | a;
}

// crc32 는 팩 색인의 항목 CRC(SPEC.md §13.2) — 반사 다항식 0xedb88320,
// 바이트마다 256칸 표를 한 번 찾는다.
uint32_t crc32(std::string_view data) {
    static const auto table = [] {
        std::array<uint32_t, 256> t{};
        for (uint32_t n = 0; n < 256; ++n) {
            uint32_t c = n;
            for (int k = 0; k < 8; ++k)
                c = c & 1 ? 0xedb88320 ^ (c >> 1) : c >> 1;
            t[n] = c;
        }
        return t;
    }();
    uint32_t c = 0xffffffff;
    for (unsigned char x : data) c = table[(c ^ x) & 0xff] ^ (c >> 8);
    return c ^ 0xffffffff;
}
}  // namespace mygit
