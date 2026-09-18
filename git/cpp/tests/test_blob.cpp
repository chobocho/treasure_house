// blob — hash-object · cat-file 의 시험. SPEC.md §1 · §9, 3단계.
// 오라클은 golden/objects/ 의 blob 들과 golden/errors.tsv 의 오류
// 문장이다. 명령은 run() 으로 과정 안에서 부른다.
#include "golden.hpp"

using namespace mygit;

namespace {
std::string body_of(const std::string& oid) {
    auto raw = decompress(golden::read("objects/" + oid));
    return raw.substr(raw.find('\0') + 1);
}
const std::string hello = "ce013625030ba8dba906f756967f9e9ca394464a";
}  // namespace

TEST(s9_hash_object_golden_blobs) {
    golden::Sandbox s(true);
    int n = 0;
    for (auto& r : golden::tsv("objects/objects.tsv")) {
        if (r["type"] != "blob") continue;
        s.put("f", body_of(r["id"]));
        auto res = s.mygit({"hash-object", "f"});
        CHECK_EQ(res.code, 0);
        CHECK_EQ(res.out, r["id"] + "\n");
        CHECK_EQ(res.err, "");
        ++n;
    }
    CHECK(n >= 3);
}

TEST(s9_stdin_and_type) {
    golden::Sandbox s(true);
    CHECK_EQ(s.run("hello\n", {"hash-object", "--stdin"}).out,
             hello + "\n");
    CHECK_EQ(s.mygit({"hash-object", "-t", "tree", "--stdin"}).out,
             "4b825dc642cb6eb9a060e54bf8d69288fbee4904\n");
}

TEST(s9_write_then_read_back) {
    golden::Sandbox s(true);
    auto data = golden::make("counter:5000");
    s.put("f", data);
    auto oid = s.mygit({"hash-object", "-w", "f"}).out.substr(0, 40);
    CHECK_EQ(s.mygit({"cat-file", "-t", oid}).out, "blob\n");
    CHECK_EQ(s.mygit({"cat-file", "-s", oid}).out, "5000\n");
    CHECK(s.mygit({"cat-file", "-p", oid}).out == data);
    // 앞부분 7글자로도 찾는다
    CHECK(s.mygit({"cat-file", "-p", oid.substr(0, 7)}).out == data);
}

TEST(s1_4_errors) {
    golden::Sandbox s(true);
    for (auto cmd : {"hash-object nope", "cat-file -p nope"}) {
        auto [line, exit] = golden::error_row(cmd);
        auto args = golden::split(cmd, ' ');
        auto r = s.mygit(args);
        CHECK_EQ(golden::first_line(r.err), line);
        CHECK_EQ(r.code, exit);
    }
}

TEST(s9_cat_file_commit_tag_blob) {
    golden::Sandbox s(true);
    for (auto& r : golden::tsv("objects/objects.tsv")) {
        if (r["type"] == "tree") continue;
        golden::plant(s.root + "/.git", r["id"]);
        auto res = s.mygit({"cat-file", "-p", r["id"]});
        CHECK_EQ(res.code, 0);
        CHECK(res.out == body_of(r["id"]));
        CHECK_EQ(s.mygit({"cat-file", "-t", r["id"]}).out,
                 r["type"] + "\n");
    }
}

TEST(s1_outside_repo) {
    golden::Sandbox s(false);
    auto [line, exit] = golden::error_row("status");
    auto r = s.mygit({"cat-file", "-t", "abcd"});
    CHECK_EQ(golden::first_line(r.err), line);
    CHECK_EQ(r.code, exit);
    s.put("f", "hello\n");
    CHECK_EQ(s.mygit({"hash-object", "f"}).code, 0);  // §1.1
    r = s.mygit({"frobnicate"});
    CHECK_EQ(r.code, 1);
    CHECK_EQ(r.err, "mygit: 'frobnicate' is not a mygit command.\n");
}
