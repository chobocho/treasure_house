// 인덱스의 시험 — SPEC.md §7, 6단계 "인덱스 — 스테이징의 실체".
// golden/index/ 의 세 파일은 진짜 git 이 쓴 인덱스다: 확장 없음,
// TREE 확장(git commit 뒤), 판 3(skip-worktree 가 켜진 항목).
// plain.bin 은 plain.raw 의 stat 칸을 §7.3 으로 지운 것이다.
#include <sys/stat.h>

#include <cstdio>

#include "golden.hpp"

using namespace mygit;

namespace {
std::string unquote(const std::string& p);

// ls_stage 는 golden/index/ls-stage.txt → "모드 이름 단계\t경로" 들.
std::vector<std::string> ls_stage() {
    std::vector<std::string> out;
    for (auto& line :
         golden::split(golden::read("index/ls-stage.txt"), '\n'))
        if (!line.empty()) {
            auto tab = line.find('\t');
            out.push_back(line.substr(0, tab + 1) +
                          unquote(line.substr(tab + 1)));
        }
    return out;
}

std::vector<std::string> summary(const std::vector<IndexEntry>& ents) {
    std::vector<std::string> out;
    for (auto& e : ents) {
        char mode[8];
        std::snprintf(mode, sizeof mode, "%06o", e.mode);
        out.push_back(std::string(mode) + " " + e.oid + " " +
                      std::to_string(e.stage) + "\t" + e.path);
    }
    return out;
}

std::string unquote(const std::string& p) {
    if (p.empty() || p[0] != '"') return p;
    std::string out;
    for (size_t i = 1; i + 1 < p.size(); ++i) {
        if (p[i] != '\\') {
            out += p[i];
        } else if (std::isdigit(uint8_t(p[i + 1]))) {
            out += char(std::stoi(p.substr(i + 1, 3), nullptr, 8));
            i += 3;
        } else {
            char n = p[++i];
            out += n == 't' ? '\t' : n == 'n' ? '\n' : n;
        }
    }
    return out;
}
}  // namespace

TEST(s7_1_read_git_indexes) {
    for (auto name : {"plain.raw", "tree-ext.raw", "v3.raw"})
        CHECK(summary(parse_index(golden::read(std::string("index/") +
                                               name))) == ls_stage());
    std::vector<std::string> skip;
    for (auto& e : parse_index(golden::read("index/v3.raw")))
        if (e.skip_worktree) skip.push_back(e.path);
    CHECK(skip == std::vector<std::string>{"run.sh"});
    auto raw = golden::read("index/plain.raw");
    raw.back() ^= 1;
    golden::git_error([&] { parse_index(raw); });
}

TEST(s7_2_s7_3_write) {
    auto raw = golden::read("index/plain.raw");
    auto ents = parse_index(raw);
    CHECK(serialize_index(ents) == raw);  // 왕복이 바이트까지 같다
    for (auto& e : ents)
        e.ctime_s = e.ctime_ns = e.mtime_s = e.mtime_ns = e.dev =
            e.ino = e.uid = e.gid = 0;
    CHECK(serialize_index(ents) == golden::read("index/plain.bin"));
    auto v3 =
        serialize_index(parse_index(golden::read("index/v3.raw")));
    CHECK(v3.substr(4, 4) == std::string("\0\0\0\2", 4));
}

TEST(s7_2_long_path_and_padding) {
    for (size_t n : {1, 2, 7, 8, 9, 100, 4094, 4095, 4096, 5000}) {
        auto e = index_entry("d/" + std::string(n, 'x'),
                             std::string(40, '1'), 0100644);
        auto data = serialize_index({e});
        // 항목 길이는 8의 배수, NUL 은 1‥8 개
        size_t body = data.size() - 12 - 20;
        CHECK_EQ(body % 8, size_t(0));
        size_t pad = body - 62 - e.path.size();
        CHECK(pad >= 1 && pad <= 8);
        CHECK_EQ(parse_index(data)[0].path, e.path);
    }
}

TEST(s7_1_sorted_by_path_then_stage) {
    std::vector<IndexEntry> ents;
    for (auto [p, s] : {std::pair{"b", 0},
                        {"a/x", 0},
                        {"a-b", 0},
                        {"c", 3},
                        {"c", 1},
                        {"c", 2}})
        ents.push_back(
            index_entry(p, std::string(40, '1'), 0100644, s));
    std::vector<std::string> got;
    for (auto& e : parse_index(serialize_index(ents)))
        got.push_back(e.path + ":" + std::to_string(e.stage));
    CHECK((got == std::vector<std::string>{"a-b:0", "a/x:0", "b:0",
                                           "c:1", "c:2", "c:3"}));
}

TEST(s7_2_exec_bit_and_size) {
    golden::TempDir t;
    auto p = t.path + "/run.sh";
    golden::write_file(p, "#!/bin/sh\n");
    chmod(p.c_str(), 0755);
    auto e = entry_from_stat("run.sh", p, std::string(40, '2'));
    CHECK_EQ(e.mode, 0100755u);
    CHECK_EQ(e.size, 10u);
    chmod(p.c_str(), 0644);
    e = entry_from_stat("run.sh", p, std::string(40, '2'));
    struct stat st;
    stat(p.c_str(), &st);
    CHECK_EQ(e.mode, 0100644u);
    CHECK_EQ(e.mtime_s, uint32_t(st.st_mtim.tv_sec));
    CHECK_EQ(e.mtime_ns, uint32_t(st.st_mtim.tv_nsec));
}

TEST(s7_4_write_and_read_back) {
    golden::TempDir t;
    auto g = golden::gitdir(t);
    CHECK(read_index(g).empty());
    write_index(g, {index_entry("a", std::string(40, '3'), 0100644)});
    CHECK((summary(read_index(g)) ==
           std::vector<std::string>{"100644 " + std::string(40, '3') +
                                    " 0\ta"}));
    CHECK(!golden::fs::exists(g + "/index.lock"));
}
