// 3-way 파일 합치기의 시험 — SPEC.md §12.3, 10단계.
// 큰 오라클은 golden/scen/merge-*.scn 14장면이다. 여기서는 merge3
// 하나를 따로 부른다 — 장면의 세 판을 그대로 넣고, 장면에서 git 이
// 남긴 파일 내용과 같은지 본다. 규칙마다 한 장면이 증거다.
#include "golden.hpp"

using namespace mygit;

namespace {
std::pair<std::string, int> merge_case(const std::string& base,
                                       const std::string& ours,
                                       const std::string& theirs) {
    return merge3(golden::make(base), golden::make(ours),
                  golden::make(theirs), "t");
}
}  // namespace

TEST(s12_3_adjacent_lines_conflict) {
    // merge-adjacent.scn — 둘째 줄과 셋째 줄을 따로 고쳐도 충돌
    auto [text, n] =
        merge_case("text:a\\nb\\nc\\nd\\n", "text:a\\nB\\nc\\nd\\n",
                   "text:a\\nb\\nC\\nd\\n");
    CHECK_EQ(n, 1);
    CHECK_EQ(text,
             "a\n<<<<<<< HEAD\nB\nc\n=======\nb\nC\n>>>>>>> t\nd\n");
}

TEST(s12_3_one_line_apart_is_clean) {
    auto [text, n] = merge_case("text:a\\nb\\nc\\nd\\ne\\n",
                                "text:a\\nB\\nc\\nd\\ne\\n",
                                "text:a\\nb\\nc\\nD\\ne\\n");
    CHECK_EQ(n, 0);
    CHECK_EQ(text, "a\nB\nc\nD\ne\n");
}

TEST(s12_3_refine_keeps_common_lines_outside) {
    auto [text, n] =
        merge_case("text:a\\nb\\nz\\n", "text:a\\nq\\nw\\ne\\nz\\n",
                   "text:a\\nq\\nr\\ne\\nz\\n");
    CHECK_EQ(n, 1);
    CHECK_EQ(text,
             "a\nq\n<<<<<<< HEAD\nw\n=======\nr\n>>>>>>> t\ne\nz\n");
}

TEST(s12_3_three_lines_apart_join_four_split) {
    CHECK_EQ(merge_case("text:a\\nb\\nm1\\nm2\\nm3\\nd\\ne\\n",
                        "text:a\\n1\\nm1\\nm2\\nm3\\n2\\ne\\n",
                        "text:a\\n3\\nm1\\nm2\\nm3\\n4\\ne\\n")
                 .second,
             1);
    CHECK_EQ(merge_case("text:a\\nb\\nm1\\nm2\\nm3\\nm4\\nd\\ne\\n",
                        "text:a\\n1\\nm1\\nm2\\nm3\\nm4\\n2\\ne\\n",
                        "text:a\\n3\\nm1\\nm2\\nm3\\nm4\\n4\\ne\\n")
                 .second,
             2);
}

TEST(s12_3_identical_change_taken_once) {
    auto [text, n] = merge_case("seq:1:5", "text:1\\nX\\n3\\n4\\n5\\n",
                                "text:1\\nX\\n3\\n4\\nY\\n");
    CHECK_EQ(n, 0);
    CHECK_EQ(text, "1\nX\n3\n4\nY\n");
}

TEST(s12_1_unborn_head_is_refused) {
    // 첫 커밋 전 — git 은 <b> 를 그대로 가져오지만 mygit 은 줄인다
    golden::Sandbox s(false);
    for (auto& [k, v] : golden::ident_env()) s.env[k] = v;
    s.mygit({"init"});
    auto tree = s.mygit({"write-tree"}).out.substr(0, 40);
    auto other = s.mygit({"commit-tree", tree, "-m", "x"}).out;
    other.pop_back();
    auto r = s.mygit({"merge", other});
    CHECK_EQ(r.code, 128);
    CHECK_EQ(r.err, "fatal: mygit: nothing to merge into yet\n");
}
