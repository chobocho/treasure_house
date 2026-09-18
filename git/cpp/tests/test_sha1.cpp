// sha1 의 시험 — SPEC.md §2 · 부록 A 1단계. 기준은 golden/sha1.tsv
// 100줄(sha1sum · git hash-object). 55·56·64 바이트 언저리의 덧붙임
// 경계가 벡터 안에 촘촘히 들어 있다.
#include "golden.hpp"

using namespace mygit;

TEST(s2_vectors) {
    auto rows = golden::tsv("sha1.tsv");
    CHECK_EQ(rows.size(), size_t(100));
    for (auto& r : rows) {
        auto data = golden::make(r["recipe"]);
        CHECK_EQ(std::to_string(data.size()), r["len"]);
        CHECK_EQ(sha1_hex(data), r["sha1"]);
        auto blob = "blob " + std::to_string(data.size()) +
                    std::string(1, '\0') + data;
        CHECK_EQ(sha1_hex(blob), r["blob"]);
    }
}

TEST(s2_streaming) {
    auto data = golden::make("counter:100000");
    auto want = sha1_hex(data);
    for (size_t size : {1, 3, 63, 64, 65, 1000, 99999}) {
        Sha1 h;
        for (size_t k = 0; k < data.size(); k += size)
            h.update(std::string_view(data).substr(k, size));
        auto d = h.digest();
        // digest 는 두 번 불러도 같다 — 상태를 바꾸지 않는다
        CHECK(d == h.digest());
        CHECK_EQ(to_hex(std::string(d.begin(), d.end())), want);
    }
}

TEST(s2_hex_round_trip) {
    std::string raw("\x00\x01\xab\xff", 4);
    CHECK_EQ(to_hex(raw), "0001abff");
    CHECK_EQ(from_hex("0001abff"), raw);
}
