// 팩의 시험 — SPEC.md §13, 11단계 "packfile — 읽기, 그다음 쓰기".
// golden/pack/ 은 진짜 git 이 쓴 팩 둘이다 — ofs(repack 이 쓴,
// OFS_DELTA)와 ref(pack-objects 가 쓴, REF_DELTA). .verify 는 git
// verify-pack -v, .show-index 는 git show-index 의 출력이다. 가장 강한
// 시험은 git 의 팩에서 다시 만든 색인이 git 의 .idx 와 바이트까지
// 같은가다.
#include <algorithm>
#include <cstdio>
#include <set>

#include "golden.hpp"

using namespace mygit;

namespace {
const char* names[] = {"ofs", "ref"};

// show_index 는 git show-index → "자리 이름 crc" 들, 정렬.
std::vector<std::string> show_index(const std::string& name) {
    std::vector<std::string> rows;
    for (auto& line : golden::split(
             golden::read("pack/" + name + ".show-index"), '\n')) {
        auto f = golden::split(line, ' ');
        if (f.size() == 3)
            rows.push_back(f[0] + " " + f[1] + " " +
                           f[2].substr(1, f[2].size() - 2));
    }
    std::sort(rows.begin(), rows.end());
    return rows;
}
}  // namespace

TEST(s13_1_every_object_and_its_delta_chain) {
    for (std::string name : names) {
        auto ents = read_pack(golden::read("pack/" + name + ".pack"));
        std::map<std::string, std::vector<std::string>> want;
        for (auto& line : golden::split(
                 golden::read("pack/" + name + ".verify"), '\n')) {
            std::vector<std::string> f;
            for (auto& x : golden::split(line, ' '))
                if (!x.empty()) f.push_back(x);
            if (f.size() >= 5 && f[0].size() == 40) want[f[0]] = f;
        }
        CHECK_EQ(ents.size(), want.size());
        std::set<int> kinds;
        for (auto& e : ents) {
            auto& f = want[e.oid];
            // 크기 칸은 팩에 적힌 크기 — 델타면 델타의 크기(§13.3)
            auto size = e.delta ? e.delta->size() : e.body.size();
            CHECK(f.size() >= 5 && f[1] == e.type &&
                  f[2] == std::to_string(size) &&
                  f[4] == std::to_string(e.offset));
            if (f.size() > 5)
                CHECK(f[5] == std::to_string(e.depth) &&
                      f[6] == e.base);
            CHECK_EQ(hash_object(e.type, e.body), e.oid);
            kinds.insert(e.packed_type);
        }
        CHECK(kinds.count(name == "ofs" ? 6 : 7));
    }
    auto data = golden::read("pack/ofs.pack");
    data.back() ^= 1;
    golden::git_error([&] { read_pack(data); });
}

TEST(s13_2_idx_matches_show_index_and_rebuilds) {
    for (std::string name : names) {
        auto [idx, sum] =
            read_idx(golden::read("pack/" + name + ".idx"));
        std::vector<std::string> got;
        for (auto& e : idx) {
            char crc[9];
            std::snprintf(crc, sizeof crc, "%08x", e.crc);
            got.push_back(std::to_string(e.offset) + " " + e.oid + " " +
                          crc);
        }
        std::sort(got.begin(), got.end());
        CHECK(got == show_index(name));
        auto data = golden::read("pack/" + name + ".pack");
        CHECK(sum == data.substr(data.size() - 20));
        CHECK(
            write_idx(read_pack(data), data.substr(data.size() - 20)) ==
            golden::read("pack/" + name + ".idx"));
    }
}

TEST(s13_1_apply_deltas_from_git) {
    int n = 0;
    for (std::string name : names) {
        auto ents = read_pack(golden::read("pack/" + name + ".pack"));
        std::map<std::string, std::string> body;
        for (auto& e : ents) body[e.oid] = e.body;
        for (auto& e : ents)
            if (!e.base.empty()) {
                CHECK(apply_delta(body[e.base], *e.delta) == e.body);
                ++n;
            }
    }
    CHECK(n > 0);
    // 예약 명령 0 · 바탕 크기가 틀림
    golden::git_error(
        [] { apply_delta("abc", std::string("\3\1\0", 3)); });
    golden::git_error([] { apply_delta("abc", "\4\1\1x"); });
}

TEST(s13_3_make_delta) {
    // SPEC.md §13.3 의 알고리즘을 손으로 따라가 얻은 바이트:
    // 크기 32 · 34, 복사(0,16), 끼움 "XY", 복사(0,16)
    std::string base = "0123456789abcdef0123456789abcdef";
    auto target = base.substr(0, 16) + "XY" + base.substr(16);
    CHECK(make_delta(base, target) == "\x20\x22\x90\x10\x02XY\x90\x10");
    base = golden::make("counter:70000");
    std::string rev(base.rbegin(), base.rbegin() + 5000);
    for (auto t :
         {base, base.substr(0, 30000) + "!" + base.substr(30000),
          std::string(), std::string(300, 'x'), rev + base})
        CHECK(apply_delta(base, make_delta(base, t)) == t);
}

TEST(s13_3_verify_pack_is_git_verbatim) {
    golden::Sandbox s(true);
    for (std::string name : names) {
        for (auto ext : {".pack", ".idx"})
            s.put(name + ext, golden::read("pack/" + name + ext));
        auto r = s.mygit({"verify-pack", "-v", name + ".idx"});
        CHECK_EQ(r.code, 0);
        CHECK_EQ(r.out, golden::read("pack/" + name + ".verify"));
    }
}

TEST(s13_3_unpack_and_s5_2_read_packed) {
    golden::Sandbox s(true);
    auto g = s.root + "/.git";
    s.put("ofs.pack", golden::read("pack/ofs.pack"));
    CHECK_EQ(s.mygit({"unpack-pack", "ofs.pack"}).code, 0);
    for (auto& row : show_index("ofs"))
        CHECK(golden::fs::exists(
            object_path(g, golden::split(row, ' ')[1])));
    golden::Sandbox s2(true);
    auto g2 = s2.root + "/.git";
    for (auto ext : {".pack", ".idx"})
        golden::write_file(g2 + "/objects/pack/pack-x" + ext,
                           golden::read(std::string("pack/ofs") + ext));
    for (auto& row : show_index("ofs")) {
        auto oid = golden::split(row, ' ')[1];
        auto o = read_object(g2, oid);
        CHECK_EQ(hash_object(o.type, o.body), oid);
        CHECK_EQ(find_object(g2, oid.substr(0, 8)), oid);
    }
}

namespace {
std::vector<PackEntry> pack_history(bool delta) {
    golden::Sandbox s(false);
    for (auto [k, v] : {std::pair{"NAME", "A"},
                        {"EMAIL", "a@x"},
                        {"DATE", "1700000000 +0900"}})
        s.env[std::string("GIT_AUTHOR_") + k] =
            s.env[std::string("GIT_COMMITTER_") + k] = v;
    s.mygit({"init"});
    std::string body;
    for (int i = 0; i < 200; ++i)
        body += "line " + std::to_string(i) + " of a growing file\n";
    for (int v = 0; v < 4; ++v) {
        std::string extra;
        for (int k = 0; k <= v; ++k)
            extra += "extra " + std::to_string(v) + "\n";
        s.put("grow.txt", body + extra);
        s.mygit({"add", "."});
        s.mygit({"commit", "-m", "v" + std::to_string(v)});
    }
    std::vector<std::string> args{"pack-objects",
                                  ".git/objects/pack/pack"};
    if (delta) args.insert(args.begin() + 1, "--delta");
    auto sha = s.mygit(args).out.substr(0, 40);
    auto g = s.root + "/.git";
    auto stem = g + "/objects/pack/pack-" + sha;
    auto data = golden::read_file(stem + ".pack");
    CHECK_EQ(to_hex(data.substr(data.size() - 20)), sha);
    auto ents = read_pack(data);
    auto [idx, _] = read_idx(golden::read_file(stem + ".idx"));
    std::vector<std::string> a, b;
    for (auto& e : idx) a.push_back(e.oid);
    for (auto& e : ents) b.push_back(e.oid);
    std::sort(a.begin(), a.end());
    std::sort(b.begin(), b.end());
    CHECK(a == b);
    CHECK(b == all_loose(g));
    return ents;
}
}  // namespace

TEST(s13_3_pack_objects) {
    for (auto& e : pack_history(false)) CHECK(e.packed_type < 5);
    std::vector<int> depths;
    for (auto& e : pack_history(true))
        if (e.packed_type == 6) depths.push_back(e.depth);
    std::sort(depths.begin(), depths.end());
    // 옛 판 셋이 한 판씩 새것을 바탕으로 — 깊이 1·2·3
    CHECK((depths == std::vector<int>{1, 2, 3}));
}
