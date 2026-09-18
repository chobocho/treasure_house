// tree 의 시험 — SPEC.md §4.3 · §8.2, 4단계 "정렬 규칙이 전부다".
// 오라클은 golden/trees/ — 경우마다 진짜 git 이 인덱스에 올린 목록
// (<경우>.tsv), write-tree 의 이름(trees.tsv), ls-tree -r -t 의 출력
// (<경우>.ls).
#include "golden.hpp"

using namespace mygit;

namespace {
std::vector<PathEntry> entries_of(const std::string& c) {
    std::vector<PathEntry> out;
    for (auto& line :
         golden::split(golden::read("trees/" + c + ".tsv"), '\n')) {
        if (line.empty() || line[0] == '#') continue;
        auto t1 = line.find('\t'), t2 = line.find('\t', t1 + 1);
        out.push_back({line.substr(0, t1),
                       line.substr(t1 + 1, t2 - t1 - 1),
                       line.substr(t2 + 1)});
    }
    return out;
}

// unquote 는 git 이 C 식으로 감싼 경로를 바이트로 되돌린다(시험 전용).
std::string unquote(const std::string& p) {
    if (p.empty() || p[0] != '"') return p;
    std::string s = p.substr(1, p.size() - 2), out;
    const std::string esc = "abtnvfr\"\\";
    const char val[] = {7, 8, 9, 10, 11, 12, 13, '"', '\\'};
    for (size_t i = 0; i < s.size(); ++i) {
        if (s[i] != '\\') {
            out += s[i];
        } else if (auto k = esc.find(s[i + 1]); k != esc.npos) {
            out += val[k], ++i;
        } else {
            out += char(std::stoi(s.substr(i + 1, 3), nullptr, 8));
            i += 3;
        }
    }
    return out;
}
}  // namespace

TEST(s4_3_twelve_trees_have_git_names) {
    auto cases = golden::tsv("trees/trees.tsv");
    CHECK_EQ(cases.size(), size_t(12));
    for (auto& r : cases) {
        golden::TempDir t;
        auto g = golden::gitdir(t);
        auto ents = entries_of(r["case"]);
        auto oid = write_tree(g, ents);
        CHECK_EQ(oid, r["tree"]);
        for (auto& line : golden::split(
                 golden::read("trees/" + r["case"] + ".ls"), '\n')) {
            auto meta =
                golden::split(line.substr(0, line.find('\t')), ' ');
            if (meta.size() == 3 && meta[1] == "tree")
                CHECK_EQ(read_object(g, meta[2]).type, "tree");
        }
        CHECK(flatten_tree(g, oid) == ents);
    }
}

TEST(s4_3_directory_sorts_as_if_it_ended_in_slash) {
    std::string z(40, '0');
    auto body = serialize_tree({{"100644", "ab", z},
                                {"40000", "a", z},
                                {"100644", "a=b", z},
                                {"100644", "a.b", z},
                                {"100644", "a-b", z}});
    std::vector<std::string> names;
    for (auto& e : parse_tree(body)) names.push_back(e.name);
    CHECK((names ==
           std::vector<std::string>{"a-b", "a.b", "a", "a=b", "ab"}));
    // 이름만으로 정렬하면 a 가 맨 앞 — 규칙이 왜 있는지 보여 준다
    CHECK(tree_entry_key("100644", "a-b") < tree_entry_key(DIR, "a"));
    CHECK(tree_entry_key("100644", "a") <
          tree_entry_key("100644", "a-b"));
    CHECK(serialize_tree({{DIR, "d", std::string(40, '1')}})
              .starts_with(std::string("40000 d\0", 8)));
    golden::git_error(
        [] { parse_tree(std::string("100644 x\0abc", 12)); });
}

TEST(s4_3_round_trip_on_git_trees) {
    int n = 0;
    for (auto& r : golden::tsv("objects/objects.tsv")) {
        if (r["type"] != "tree") continue;
        auto raw = decompress(golden::read("objects/" + r["id"]));
        auto body = raw.substr(raw.find('\0') + 1);
        CHECK(serialize_tree(parse_tree(body)) == body);
        ++n;
    }
    CHECK(n >= 2);
}

TEST(s8_2_quoting) {
    CHECK_EQ(quote_path("plain.txt"), "plain.txt");
    CHECK_EQ(quote_path("sp ace"), "sp ace");
    CHECK_EQ(quote_path("sp ace", true), "\"sp ace\"");
    CHECK_EQ(quote_path("tab\tx"), "\"tab\\tx\"");
    CHECK_EQ(quote_path("q\"uote"), "\"q\\\"uote\"");
    CHECK_EQ(quote_path("back\\slash"), "\"back\\\\slash\"");
    CHECK_EQ(quote_path("한글.txt"),
             "\"\\355\\225\\234\\352\\270\\200.txt\"");
    CHECK_EQ(quote_path("del\x7f"), "\"del\\177\"");
}

TEST(s9_cat_file_p_tree_matches_ls_tree) {
    for (auto& r : golden::tsv("trees/trees.tsv")) {
        golden::Sandbox s(true);
        write_tree(s.root + "/.git", entries_of(r["case"]));
        std::string want;
        for (auto& line : golden::split(
                 golden::read("trees/" + r["case"] + ".ls"), '\n')) {
            auto tab = line.find('\t');
            if (tab != line.npos &&
                unquote(line.substr(tab + 1)).find('/') ==
                    std::string::npos)
                want += line + "\n";
        }
        auto res = s.mygit({"cat-file", "-p", r["tree"]});
        CHECK_EQ(res.code, 0);
        CHECK_EQ(res.out, want);
    }
}
