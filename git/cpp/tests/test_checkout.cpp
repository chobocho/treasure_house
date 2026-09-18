// 작업 트리 바꾸기의 시험 — SPEC.md §9.3, 9단계 "checkout · switch".
// 큰 오라클은 golden/scen/checkout.scn 이다. 여기서는 장면이 직접 보지
// 않는 두 가지 — 파일이 없어져 비게 된 디렉터리가 지워지는가, 실행
// 비트가 작업 트리에 살아나는가 — 를 본다. git 도 둘 다 그렇게 한다.
#include <sys/stat.h>

#include "golden.hpp"

using namespace mygit;

namespace {
// Repo 는 mygit init 으로 시작한 저장소 — ok 는 코드 0 을 요구한다.
struct Repo : golden::Sandbox {
    Repo() : Sandbox(false) {
        for (auto [k, v] : {std::pair{"NAME", "A"},
                            {"EMAIL", "a@x"},
                            {"DATE", "1700000000 +0900"}}) {
            env[std::string("GIT_AUTHOR_") + k] = v;
            env[std::string("GIT_COMMITTER_") + k] = v;
        }
        ok({"init"});
    }
    std::string ok(std::vector<std::string> args) {
        auto r = mygit(args);
        CHECK_EQ(r.code, 0);
        if (r.code) throw std::runtime_error(args[0] + ": " + r.err);
        return r.out;
    }
    void put(const std::string& rel, const std::string& data,
             int mode = 0644) {
        golden::write_file(root + "/" + rel, data);
        ::chmod((root + "/" + rel).c_str(), mode);
    }
};
}  // namespace

TEST(s9_3_emptied_directories_are_removed) {
    Repo r;
    r.put("keep", "k\n");
    r.ok({"add", "."});
    r.ok({"commit", "-m", "base"});
    r.ok({"switch", "-c", "deep"});
    r.put("a/b/c.txt", "c\n");
    r.ok({"add", "."});
    r.ok({"commit", "-m", "deep"});
    r.ok({"switch", "main"});
    CHECK(!golden::fs::exists(r.root + "/a"));
    r.ok({"switch", "deep"});
    CHECK_EQ(golden::read_file(r.root + "/a/b/c.txt"), "c\n");
}

TEST(s9_3_exec_bit_is_written) {
    Repo r;
    r.put("run", "#!/bin/sh\n", 0755);
    r.ok({"add", "."});
    r.ok({"commit", "-m", "x"});
    r.ok({"switch", "-c", "side"});
    golden::fs::remove(r.root + "/run");
    r.ok({"add", "."});
    r.ok({"commit", "-m", "gone"});
    r.ok({"switch", "main"});
    struct stat st;
    CHECK(::stat((r.root + "/run").c_str(), &st) == 0 &&
          (st.st_mode & 0100));
}

TEST(s9_3_status_is_clean_after_switch) {
    Repo r;
    r.put("f", "1\n");
    r.ok({"add", "."});
    r.ok({"commit", "-m", "one"});
    r.ok({"switch", "-c", "b2"});
    r.put("f", "2\n");
    r.put("g/h", "h\n");
    r.ok({"add", "."});
    r.ok({"commit", "-m", "two"});
    for (auto name : {"main", "b2", "main"}) {
        r.ok({"switch", name});
        CHECK_EQ(r.ok({"status"}), "");
    }
}
