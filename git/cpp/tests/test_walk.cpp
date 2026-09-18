// 역사 걷기·merge-base·branch -d 의 시험 — SPEC.md §9.1 · §9.2 · §10,
// 7단계. golden/dag/<역사>/git 은 진짜 git 이 만든 .git 이고,
// expect.txt 는 그 저장소에서 git 이 찍은 log·merge-base 출력이다.
// equal 은 모든 커밋의 날짜가 같고(§10.1 의 "먼저 온 것이 먼저"),
// dated 는 날짜가 모두 다르고, criss 는 가장 좋은 공통 조상이 둘이다.
#include <algorithm>

#include "golden.hpp"

using namespace mygit;

TEST(s10_log_and_merge_base_match_git) {
    int n = 0;
    for (std::string name : {"equal", "dated", "criss"}) {
        golden::Sandbox s(false);
        golden::dag(s, name);
        auto text = golden::read("dag/" + name + "/expect.txt");
        auto blocks = golden::split(text, '$');
        for (size_t k = 1; k < blocks.size(); ++k) {
            auto& b = blocks[k];  // " git <명령>\n<출력>= <코드>\n"
            auto nl = b.find('\n');
            auto cmd = b.substr(5, nl - 5);
            auto at = b.rfind("= ");
            auto r = s.mygit(golden::split(cmd, ' '));
            CHECK_EQ(r.out, b.substr(nl + 1, at - nl - 1));
            CHECK_EQ(r.code, std::stoi(b.substr(at + 2)));
            ++n;
        }
    }
    CHECK(n >= 14);
}

TEST(s10_1_walk_and_is_ancestor) {
    golden::Sandbox s(false);
    golden::dag(s, "equal");
    auto g = s.root + "/.git";
    auto head = rev_parse(g, "HEAD"), t = rev_parse(g, "t");
    auto order = walk_log(g, {head});
    CHECK_EQ(order.size(), size_t(11));
    CHECK_EQ(order[0], head);
    CHECK(is_ancestor(g, t, head));
    CHECK(!is_ancestor(g, head, t));
    CHECK(is_ancestor(g, head, head));
}

TEST(s9_2_branch_delete) {
    golden::Sandbox s(false);
    golden::dag(s, "equal");
    auto g = s.root + "/.git";
    auto t = rev_parse(g, "t");
    auto r = s.mygit({"branch", "-d", "t"});
    CHECK_EQ(r.code, 0);
    CHECK_EQ(r.out, "Deleted branch t (was " + t.substr(0, 7) + ").\n");
    CHECK_EQ(resolve_ref(g, "refs/heads/t"), "");
    r = s.mygit({"branch", "-d", "main"});
    CHECK_EQ(r.code, 1);
    CHECK_EQ(
        r.err,
        "error: cannot delete branch 'main' used by worktree at '" +
            s.root + "'\n");
    s.mygit({"branch", "old", "HEAD~1"});
    // HEAD 를 뒤로 돌려 old 가 HEAD 에서 닿지 않게 한다
    set_head(g, rev_parse(g, "HEAD~2"));
    r = s.mygit({"branch", "-d", "old"});
    CHECK_EQ(r.code, 1);
    CHECK_EQ(r.err, "error: the branch 'old' is not fully merged\n");
}

TEST(s1_4_log_errors_and_limit) {
    golden::Sandbox s(false);
    golden::dag(s, "equal");
    auto r = s.mygit({"log", "nope"});
    CHECK_EQ(r.code, 128);
    CHECK_EQ(
        golden::first_line(r.err),
        "fatal: ambiguous argument 'nope': unknown revision or path "
        "not in the working tree.");
    r = s.mygit({"log", "--oneline", "-n", "3"});
    CHECK_EQ(std::count(r.out.begin(), r.out.end(), '\n'), 3);
}
