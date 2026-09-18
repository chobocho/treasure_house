// 전송의 시험 — SPEC.md §14, 12단계 "pkt-line 으로 진짜 git 과 대화".
// fetch-pack 은 진짜 git upload-pack 을 자식으로 띄워 말한다(PLAN.md
// §9 결정 8 — 서버는 git 이다). golden/pkt/<경우>.log 는 SPEC §14.3 의
// 요청을 그대로 보냈을 때 git 이 돌려준 대화의 기록이고, mygit 의
// 기록은 글자까지 같아야 한다. 받은 팩 바이트와 표준 출력도 같아야
// 한다. 멍청한 clone 은 golden/scen/clone.scn 이 장면 시험으로 본다.
#include "golden.hpp"

using namespace mygit;

TEST(s14_1_pkt_line_and_render) {
    CHECK_EQ(pkt_line("a\n"), "0006a\n");
    CHECK_EQ(pkt_line(""), "0004");
    CHECK_EQ(pkt_line(std::string(65516, 'x')).substr(0, 4), "fff0");
    golden::git_error([] { pkt_line(std::string(65517, 'x')); });
    CHECK_EQ(render("command=ls-refs\n"), "0014command=ls-refs\\n");
    // 파이썬 repr 의 꼴 — 따옴표 고르기까지 같아야 기록이 같다
    CHECK_EQ(render("a'b"), "0007a'b");
    CHECK_EQ(render("a'b\""), "0008a\\'b\"");
    CHECK_EQ(render(std::string("\0\xff\\\t", 4)),
             "0008\\x00\\xff\\\\\\t");
}

namespace {
struct Fetched {
    Result r;
    std::string log, gitdir;
};

// fetch 는 golden/pkt/src 를 원본으로, 빈 저장소에서 fetch-pack 을
// 돌린다. 가진 값이 있는 경우는 원본의 객체를 넣고 참조를 세운다.
Fetched fetch(golden::Sandbox& s, const std::string& c) {
    auto src = s.t.path + "/src/.git";
    golden::copy_tree("golden/pkt/src/git", src);
    for (auto d : {"objects/pack", "refs/tags"})
        golden::fs::create_directories(src + "/" + d);
    s.mygit({"init"});
    auto g = s.root + "/.git";
    auto args = golden::split(golden::read("pkt/" + c + ".args"), '\n');
    if (!args[1].empty()) {
        golden::fs::remove_all(g + "/objects");
        golden::copy_tree(src + "/objects", g + "/objects");
        update_ref(g, "refs/heads/old", args[1], "", "test",
                   "T <t@t> 0 +0000");
    }
    auto log = s.t.path + "/" + c + ".log";
    s.env["MYGIT_PKT_LOG"] = log;
    std::vector<std::string> cmd{"fetch-pack", s.t.path + "/src"};
    for (auto& w : golden::split(args[0], ' ')) cmd.push_back(w);
    auto r = s.mygit(cmd);
    return {r, golden::read_file(log), g};
}
}  // namespace

TEST(s14_3_conversation_matches_git) {
    for (std::string c : {"full", "two-refs", "have-first"}) {
        golden::Sandbox s(false);
        auto f = fetch(s, c);
        CHECK_EQ(f.r.code, 0);
        CHECK_EQ(f.r.err, "");
        CHECK_EQ(f.r.out, golden::read("pkt/" + c + ".stdout"));
        CHECK_EQ(f.log, golden::read("pkt/" + c + ".log"));
    }
}

TEST(s14_3_received_pack_is_stored_and_readable) {
    golden::Sandbox s(false);
    auto f = fetch(s, "full");
    auto want = golden::read("pkt/full.pack");
    auto name =
        "pack-" + to_hex(want.substr(want.size() - 20)) + ".pack";
    CHECK(golden::read_file(f.gitdir + "/objects/pack/" + name) ==
          want);
    CHECK_EQ(read_object(f.gitdir, f.r.out.substr(0, 40)).type,
             "commit");
}
