// inflate — RFC 1950(zlib) 겉옷 속의 RFC 1951(deflate)을 손으로 푼다
// (SPEC.md §3.2). 진짜 git 이 쓴 객체는 고정 허프만(BTYPE=01)·동적
// 허프만(BTYPE=10) 블록이라, 저장 블록만 쓰는 이 구현도 읽기는 셋 다
// 해야 한다. 허프만 부호는 "길이마다 부호 몇 개" 와 "부호 차례의 기호"
// 두 표로 푼다(정준 허프만, zlib 의 puff.c 와 같은 방법).
// O(출력 길이 × 부호 길이) 시간, O(출력) 공간.
#include "mygit.hpp"

namespace mygit {
namespace {
const std::string corrupt = "fatal: mygit: corrupt zlib stream";

// Bits 는 입력을 작은 쪽 비트부터 읽는다(deflate 의 비트 차례).
struct Bits {
    std::string_view in;
    size_t pos;
    uint32_t buf = 0;
    int cnt = 0;

    uint32_t need(int n) {
        while (cnt < n) {
            if (pos >= in.size())
                throw GitError("fatal: mygit: truncated zlib stream");
            buf |= uint32_t(uint8_t(in[pos++])) << cnt;
            cnt += 8;
        }
        uint32_t v = buf & ((1u << n) - 1);
        buf >>= n;
        cnt -= n;
        return v;
    }
    void align() { buf = 0, cnt = 0; }  // 남은 비트는 버린다
};

struct Huffman {
    uint16_t count[16] = {};       // 길이마다 부호의 수
    std::vector<uint16_t> symbol;  // 부호 차례로 늘어선 기호
};

// build 는 기호마다의 부호 길이 → 정준 허프만 표. 부호가 넘치면
// (과잉 부호) 깨진 스트림이다.
Huffman build(const uint8_t* lengths, int n) {
    Huffman h;
    for (int s = 0; s < n; ++s) h.count[lengths[s]]++;
    int left = 1;
    for (int len = 1; len < 16; ++len) {
        left = left * 2 - h.count[len];
        if (left < 0) throw GitError(corrupt);
    }
    uint16_t offs[16] = {};
    for (int len = 1; len < 15; ++len)
        offs[len + 1] = offs[len] + h.count[len];
    h.symbol.resize(n);
    for (int s = 0; s < n; ++s)
        if (lengths[s]) h.symbol[offs[lengths[s]]++] = uint16_t(s);
    return h;
}

// decode 는 비트를 하나씩 붙이며 그 길이의 부호 범위에 드는지 본다.
int decode(Bits& b, const Huffman& h) {
    int code = 0, first = 0, index = 0;
    for (int len = 1; len < 16; ++len) {
        code |= int(b.need(1));
        int count = h.count[len];
        if (code - count < first) return h.symbol[index + code - first];
        index += count;
        first = (first + count) << 1;
        code <<= 1;
    }
    throw GitError(corrupt);
}

const uint16_t len_base[] = {
    3,  4,  5,  6,  7,  8,  9,  10, 11,  13,  15,  17,  19,  23, 27,
    31, 35, 43, 51, 59, 67, 83, 99, 115, 131, 163, 195, 227, 258};
const uint8_t len_extra[] = {0, 0, 0, 0, 0, 0, 0, 0, 1, 1,
                             1, 1, 2, 2, 2, 2, 3, 3, 3, 3,
                             4, 4, 4, 4, 5, 5, 5, 5, 0};
const uint16_t dist_base[] = {
    1,    2,    3,    4,    5,    7,    9,    13,    17,    25,
    33,   49,   65,   97,   129,  193,  257,  385,   513,   769,
    1025, 1537, 2049, 3073, 4097, 6145, 8193, 12289, 16385, 24577};
const uint8_t dist_extra[] = {0, 0, 0,  0,  1,  1,  2,  2,  3,  3,
                              4, 4, 5,  5,  6,  6,  7,  7,  8,  8,
                              9, 9, 10, 10, 11, 11, 12, 12, 13, 13};

// codes 는 한 블록의 기호들을 푼다: 0‥255 는 바이트, 256 은 끝,
// 257‥285 는 (길이, 거리) — 이미 낸 출력에서 거리만큼 뒤를 복사한다.
void codes(Bits& b, std::string& out, const Huffman& lit,
           const Huffman& dist) {
    for (;;) {
        int sym = decode(b, lit);
        if (sym < 256) {
            out += char(sym);
            continue;
        }
        if (sym == 256) return;
        sym -= 257;
        if (sym >= 29) throw GitError(corrupt);
        size_t len = len_base[sym] + b.need(len_extra[sym]);
        int d = decode(b, dist);
        if (d >= 30) throw GitError(corrupt);
        size_t back = dist_base[d] + b.need(dist_extra[d]);
        if (back > out.size()) throw GitError(corrupt);
        // 겹칠 수 있어(거리 < 길이) 한 바이트씩 — 되풀이 무늬가 된다
        for (size_t k = 0; k < len; ++k) out += out[out.size() - back];
    }
}

void fixed(Bits& b, std::string& out) {
    static const auto tables = [] {
        uint8_t l[288], d[30];
        for (int s = 0; s < 288; ++s)
            l[s] = s < 144 ? 8 : s < 256 ? 9 : s < 280 ? 7 : 8;
        for (auto& x : d) x = 5;
        return std::pair{build(l, 288), build(d, 30)};
    }();
    codes(b, out, tables.first, tables.second);
}

void dynamic(Bits& b, std::string& out) {
    int nlen = int(b.need(5)) + 257, ndist = int(b.need(5)) + 1;
    int ncode = int(b.need(4)) + 4;
    if (nlen > 286 || ndist > 30) throw GitError(corrupt);
    static const uint8_t order[19] = {16, 17, 18, 0,  8, 7,  9,
                                      6,  10, 5,  11, 4, 12, 3,
                                      13, 2,  14, 1,  15};
    uint8_t lengths[316] = {};
    for (int k = 0; k < ncode; ++k)
        lengths[order[k]] = uint8_t(b.need(3));
    Huffman lencode = build(lengths, 19);
    // 부호 길이 자체도 부호다: 16 은 앞 길이를 3‥6번, 17·18 은 0 을
    // 3‥10번·11‥138번 되풀이한다
    for (int k = 0; k < nlen + ndist;) {
        int sym = decode(b, lencode);
        if (sym < 16) {
            lengths[k++] = uint8_t(sym);
            continue;
        }
        uint8_t val = 0;
        int rep;
        if (sym == 16) {
            if (k == 0) throw GitError(corrupt);
            val = lengths[k - 1];
            rep = 3 + int(b.need(2));
        } else if (sym == 17) {
            rep = 3 + int(b.need(3));
        } else {
            rep = 11 + int(b.need(7));
        }
        if (k + rep > nlen + ndist) throw GitError(corrupt);
        while (rep--) lengths[k++] = val;
    }
    if (lengths[256] == 0) throw GitError(corrupt);  // 끝 기호가 없다
    codes(b, out, build(lengths, nlen), build(lengths + nlen, ndist));
}
}  // namespace

std::pair<std::string, size_t> decompress_prefix(std::string_view data,
                                                 size_t start) {
    Bits b{data, start};
    uint32_t cmf = b.need(8), flg = b.need(8);
    if ((cmf & 15) != 8 || (cmf >> 4) > 7 || (cmf * 256 + flg) % 31 ||
        (flg & 0x20))  // 미리 정한 사전(FDICT)은 git 이 쓰지 않는다
        throw GitError(corrupt);
    std::string out;
    for (bool last = false; !last;) {
        last = b.need(1);
        switch (b.need(2)) {
            case 0: {  // 저장 블록 — 바이트 경계에서 길이·보수·날것
                b.align();
                uint32_t len = b.need(16), nlen = b.need(16);
                if ((len ^ 0xffff) != nlen) throw GitError(corrupt);
                if (b.pos + len > data.size())
                    throw GitError(
                        "fatal: mygit: truncated zlib stream");
                out.append(data.substr(b.pos, len));
                b.pos += len;
                break;
            }
            case 1:
                fixed(b, out);
                break;
            case 2:
                dynamic(b, out);
                break;
            default:
                throw GitError(corrupt);
        }
    }
    b.align();
    uint32_t want = 0;
    for (int k = 0; k < 4; ++k) want = want << 8 | b.need(8);
    if (want != adler32(out)) throw GitError(corrupt);
    return {out, b.pos - start};
}

std::string decompress(std::string_view data) {
    auto [out, used] = decompress_prefix(data, 0);
    if (used != data.size())
        throw GitError("fatal: mygit: garbage after zlib stream");
    return out;
}
}  // namespace mygit
