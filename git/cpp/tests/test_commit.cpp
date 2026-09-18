// commit·tag·신원 줄과 참조의 시험 — SPEC.md §4.4 · §4.5 · §6, 5단계.
// 가장 강한 오라클은 "같은 입력에서 같은 이름" 이다. golden/objects 의
// 커밋과 태그는 고정 환경에서 진짜 git 이 만들었다 — 같은 트리·같은
// 환경으로 만든 mygit 의 것은 바이트까지 같아야 한다.
#include <ctime>

#include "golden.hpp"

using namespace mygit;

namespace {
const std::string commit_id =
    "b23b7a5fefc32902eb83feac2800cf158140dcb1";
const std::string tag_id = "5702a431dba432bfe47c3b3fdda3835a8f542f5c";
const std::string mitter =
    "C O Mitter <committer@example.com> 1700000000 +0900";

std::string body_of(const std::string& oid) {
    auto raw = decompress(golden::read("objects/" + oid));
    return raw.substr(raw.find('\0') + 1);
}

// repo 는 mygit init 으로 만든 저장소에 golden 객체를 전부 심는다.
void repo(golden::Sandbox& s) {
    for (auto& [k, v] : golden::ident_env()) s.env[k] = v;
    CHECK_EQ(s.mygit({"init"}).code, 0);
    for (auto& r : golden::tsv("objects/objects.tsv"))
        golden::plant(s.root + "/.git", r["id"]);
}
}  // namespace

TEST(s4_4_parse_ident) {
    auto i =
        parse_ident("A U Thor <author@example.com> 1700000000 +0900");
    CHECK_EQ(i.name, "A U Thor");
    CHECK_EQ(i.mail, "author@example.com");
    CHECK_EQ(i.secs, 1700000000LL);
    CHECK_EQ(i.tz, "+0900");
}

TEST(s9_1_date_matches_git_log) {
    // golden/scen/hello.scn: git log 이 찍은 두 날짜
    CHECK_EQ(format_date(1700000000, "+0900"),
             "Wed Nov 15 07:13:20 2023 +0900");
    CHECK_EQ(format_date(1700000060, "+0900"),
             "Wed Nov 15 07:14:20 2023 +0900");
    // 달력 계산은 손으로 한다 — 표준 gmtime 은 증인으로만
    for (long long secs : {0LL, 86399LL, 951782400LL, 1700000000LL,
                           2000000000LL, 1709251199LL, 4102444800LL}) {
        for (std::string tz :
             {"+0000", "-0700", "+0530", "-1200", "+1400"}) {
            int off = std::stoi(tz.substr(1, 2)) * 3600 +
                      std::stoi(tz.substr(3)) * 60;
            time_t t = secs + (tz[0] == '-' ? -off : off);
            struct tm g;
            gmtime_r(&t, &g);
            char buf[64];
            strftime(buf, sizeof buf, "%a %b ", &g);
            char rest[32];
            strftime(rest, sizeof rest, " %H:%M:%S %Y ", &g);
            auto want = std::string(buf) + std::to_string(g.tm_mday) +
                        rest + tz;
            CHECK_EQ(format_date(secs, tz), want);
        }
    }
}

TEST(s1_3_missing_env_is_an_error) {
    auto env = golden::ident_env();
    env.erase("GIT_AUTHOR_DATE");
    CHECK_EQ(std::string(golden::git_error([&] {
                             ident_from_env(env, "AUTHOR");
                         }).what()),
             "fatal: mygit: GIT_AUTHOR_DATE is not set");
    env["GIT_AUTHOR_DATE"] = "yesterday";
    CHECK_EQ(
        std::string(golden::git_error([&] {
                        ident_from_env(env, "AUTHOR");
                    }).what()),
        "fatal: mygit: GIT_AUTHOR_DATE is not '<seconds> <+hhmm>'");
}

TEST(s4_4_cleanup_and_subject) {
    // SPEC.md §4.4 의 예 — 진짜 git commit -m 으로 확인한 것
    CHECK_EQ(cleanup_message("\n\n  lead  \n\nx   \n \n\n\ny\n\n"),
             "  lead\n\nx\n\ny\n");
    CHECK_EQ(cleanup_message("one"), "one\n");
    CHECK_EQ(cleanup_message(" \n \n"), "");
    CHECK_EQ(subject_of("second\n\nbody line\n"), "second");
    CHECK_EQ(subject_of("second\nbody line\n\npara2\n"),
             "second body line");
}

TEST(s4_4_s4_5_git_bytes) {
    auto body = body_of(commit_id);
    auto c = parse_commit(body);
    CHECK(c.parents.empty());
    CHECK(serialize_commit(c) == body);
    CHECK(serialize_tag(commit_id, "commit", "v1", mitter,
                        "tag message\n") == body_of(tag_id));
}

TEST(s5_1_init) {
    golden::Sandbox s(false);
    auto r = s.mygit({"init"});
    auto g = s.root + "/.git";
    CHECK_EQ(r.code, 0);
    CHECK_EQ(r.err, "");
    CHECK_EQ(r.out, "Initialized empty Git repository in " + g + "/\n");
    CHECK_EQ(golden::read_file(g + "/HEAD"), "ref: refs/heads/main\n");
    CHECK_EQ(
        golden::read_file(g + "/config"),
        "[core]\n\trepositoryformatversion = 0\n\tfilemode = true\n"
        "\tbare = false\n\tlogallrefupdates = true\n");
    for (auto d : {"objects/pack", "refs/heads", "refs/tags"})
        CHECK(golden::fs::is_directory(g + "/" + d));
    golden::write_file(g + "/HEAD", "ref: refs/heads/dev\n");
    CHECK_EQ(s.mygit({"init"}).out,
             "Reinitialized existing Git repository in " + g + "/\n");
    CHECK_EQ(golden::read_file(g + "/HEAD"), "ref: refs/heads/dev\n");
    CHECK_EQ(s.mygit({"init", "sub"}).code, 0);
    CHECK(golden::fs::is_directory(s.root + "/sub/.git"));
}

TEST(s4_4_commit_tree_reproduces_git) {
    golden::Sandbox s(false);
    repo(s);
    auto g = s.root + "/.git";
    auto tree = parse_commit(body_of(commit_id)).tree;
    auto r = s.mygit({"commit-tree", tree, "-m", "objects"});
    CHECK_EQ(r.code, 0);
    CHECK_EQ(r.out, commit_id + "\n");
    CHECK_EQ(r.err, "");
    r = s.mygit(
        {"commit-tree", tree, "-p", commit_id, "-m", "a", "-m", "b"});
    auto c = parse_commit(read_object(g, r.out.substr(0, 40)).body);
    CHECK(c.parents == std::vector<std::string>{commit_id});
    CHECK_EQ(c.message, "a\n\nb\n");
    r = s.mygit({"commit-tree", tree, "-m", "  m1  "});
    CHECK_EQ(
        parse_commit(read_object(g, r.out.substr(0, 40)).body).message,
        "  m1  \n");
}

TEST(s4_5_annotated_tag_reproduces_git) {
    golden::Sandbox s(false);
    repo(s);
    s.mygit({"branch", "main", commit_id});
    auto r = s.mygit({"tag", "-a", "v1", "-m", "tag message"});
    CHECK_EQ(r.code, 0);
    CHECK_EQ(r.out + r.err, "");
    CHECK_EQ(resolve_ref(s.root + "/.git", "refs/tags/v1"), tag_id);
}

TEST(s1_4_errors) {
    golden::Sandbox s(false);
    repo(s);
    s.mygit({"branch", "main", commit_id});
    for (std::string cmd :
         {"commit-tree nope -m x", "branch x nope", "tag t nope",
          "branch main", "branch a..b", "tag t"}) {
        if (cmd == "tag t") s.mygit({"tag", "t"});
        auto [line, exit] = golden::error_row(cmd);
        auto r = s.mygit(golden::split(cmd, ' '));
        CHECK_EQ(r.code, exit);
        CHECK_EQ(golden::first_line(r.err), line);
    }
}

TEST(s9_2_branch_and_s6_3_reflog) {
    golden::Sandbox s(false);
    repo(s);
    auto g = s.root + "/.git";
    CHECK_EQ(s.mygit({"branch", "main", commit_id}).code, 0);
    s.mygit({"branch", "topic", "main"});
    CHECK_EQ(s.mygit({"branch"}).out, "* main\n  topic\n");
    CHECK((read_reflog(g, "refs/heads/topic") ==
           std::vector<ReflogEntry>{{ZERO, commit_id, mitter,
                                     "branch: Created from main"}}));
    CHECK_EQ(s.mygit({"reflog", "topic"}).out,
             commit_id.substr(0, 7) +
                 " topic@{0}: branch: Created from main\n");
}

TEST(s6_3_reflog_line_bytes) {
    golden::Sandbox s(false);
    repo(s);
    auto g = s.root + "/.git";
    append_reflog(g, "HEAD", ZERO, commit_id, "X <x@y> 1 +0000",
                  "commit (initial): t");
    CHECK_EQ(golden::read_file(g + "/logs/HEAD"),
             ZERO + " " + commit_id +
                 " X <x@y> 1 +0000\tcommit (initial): t\n");
}

TEST(s6_2_rev_parse) {
    golden::Sandbox s(false);
    golden::dag(s, "equal");
    auto g = s.root + "/.git";
    // golden/dag/equal 에서 git log --oneline 이 찍은 "<차례>:<제목>"
    std::map<std::string, std::string> id;
    auto text = golden::read("dag/equal/expect.txt");
    auto block = text.substr(text.find("$ git log --oneline\n") + 20);
    block = block.substr(0, block.find("= 0"));
    int k = 0;
    for (auto& line : golden::split(block, '\n'))
        if (!line.empty())
            id[std::to_string(k++) + ":" + line.substr(8)] =
                line.substr(0, 7);
    auto rp = [&](const std::string& spec) {
        return rev_parse(g, spec).substr(0, 7);
    };
    CHECK_EQ(rp("HEAD"), id["0:I"]);
    CHECK_EQ(rp("main"), id["0:I"]);
    CHECK_EQ(rp("refs/heads/main"), id["0:I"]);
    CHECK_EQ(rp("main~1"), id["1:Merge branch 't'"]);
    CHECK_EQ(rp("HEAD~2"), id["2:G"]);    // 첫 부모
    CHECK_EQ(rp("HEAD~1^2"), id["3:H"]);  // 둘째 부모
    CHECK_EQ(rp("HEAD^^"), id["2:G"]);
    CHECK_EQ(rp("t"), id["3:H"]);
    CHECK_EQ(rp(id["2:G"]), id["2:G"]);  // 앞부분
    CHECK_EQ(rp("HEAD^0"), id["0:I"]);
    CHECK_EQ(rp("nope"), "");
    CHECK_EQ(rp("HEAD~99"), "");
    CHECK_EQ(read_object(g, rev_parse(g, "HEAD^{tree}")).type, "tree");
}
