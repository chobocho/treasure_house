// diff 의 시험 — SPEC.md §11, 8단계 "diff — Myers 알고리즘".
// golden/diff/ 는 진짜 `git -c diff.indentHeuristic=false diff
// --no-index` 의 출력이다. agree 30쌍은 바이트까지 같아야 하고, tie
// 3쌍은 git 이 같은 길이의 다른 편집 스크립트를 고르는 쌍이다 —
// 거기서는 지운 줄·끼운 줄의 수가 같고 출력은 달라야 한다(§11.2).
#include <algorithm>

#include "golden.hpp"

using namespace mygit;

namespace {
Result run_pair(golden::Sandbox& s, const std::string& stem) {
    for (auto ext : {".a", ".b"})
        s.put(stem + ext, golden::read("diff/" + stem + ext));
    return s.mygit({"diff", "--no-index", stem + ".a", stem + ".b"});
}
}  // namespace

TEST(s11_agree_pairs_are_byte_identical) {
    golden::Sandbox s(false);
    auto rows = golden::tsv("diff/agree.tsv");
    CHECK_EQ(rows.size(), size_t(30));
    for (auto& r : rows) {
        auto res = run_pair(s, r["name"]);
        CHECK_EQ(res.code, std::stoi(r["exit"]));
        CHECK(res.out == golden::read("diff/" + r["name"] + ".diff"));
        CHECK_EQ(res.err, "");
    }
}

TEST(s11_2_tie_pairs_same_size_different_choice) {
    golden::Sandbox s(false);
    auto rows = golden::tsv("diff/tie.tsv");
    CHECK_EQ(rows.size(), size_t(3));
    for (auto& r : rows) {
        auto out = run_pair(s, r["name"]).out;
        int minus = 0, plus = 0;
        for (auto& l : golden::split(out, '\n')) {
            if (l.starts_with("---") || l.starts_with("+++")) continue;
            minus += l.starts_with("-"), plus += l.starts_with("+");
        }
        CHECK_EQ(std::to_string(minus), r["minus"]);
        CHECK_EQ(std::to_string(plus), r["plus"]);
        CHECK(out != golden::read("diff/" + r["name"] + ".diff"));
    }
}

TEST(s11_pieces) {
    CHECK((split_lines("a\nb\nc") == Lines{"a\n", "b\n", "c"}));
    CHECK(split_lines("").empty());
    CHECK((split_lines("\n") == Lines{"\n"}));
    // Myers 논문 그림 1 의 예 — 가장 짧은 편집 스크립트는 5
    auto [ra, rb] = myers(split_lines("a\nb\nc\na\nb\nb\na\n"),
                          split_lines("c\nb\na\nb\na\nc\n"));
    CHECK_EQ(std::count(ra.begin(), ra.end(), true) +
                 std::count(rb.begin(), rb.end(), true),
             5);
    CHECK(unified_diff(split_lines("x\n"), {})
              .starts_with("@@ -1 +0,0 @@\n"));
    CHECK(unified_diff({}, split_lines("x\ny\n"))
              .starts_with("@@ -0,0 +1,2 @@\n"));
    CHECK(unified_diff(split_lines("same\n"), split_lines("same\n"))
              .empty());
}
