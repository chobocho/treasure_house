// 장면 시험 — golden/scen/*.scn 을 mygit 으로 다시 돌린다(SPEC.md
// §16.4). 장면의 기대 출력은 진짜 git 2.55.0 이 채웠다. 같은 명령을
// 빈 임시 디렉터리에서 mygit 으로 돌리고, 명령마다 표준 출력·표준
// 오류·종료 코드를 한 글자씩 견준다. 장면은 자기에게 필요한 명령이 다
// 생기는 단계(STEP)부터 켜진다. 12단계를 마치면 건너뛰는 장면이 없다.
#include <sys/stat.h>

#include <cstdio>

#include "golden.hpp"

using namespace mygit;

namespace {
// 장면 → 켜지는 단계 (그 장면이 쓰는 명령이 모두 생기는 단계)
int step_of(const std::string& name) {
    static const std::map<std::string, int> needs = {
        {"plumbing", 6}, {"status", 6},  {"hello", 7}, {"diff", 8},
        {"checkout", 9}, {"errors", 10}, {"clone", 12}};
    return name.starts_with("merge-") ? 10 : needs.at(name);
}

// split_args 는 SPEC.md §16.4 — 공백으로 가르고 "…" 는 한 덩어리.
std::vector<std::string> split_args(const std::string& line) {
    std::vector<std::string> args;
    std::optional<std::string> cur;
    bool quoted = false;
    for (size_t i = 0; i < line.size(); ++i) {
        char c = line[i];
        if (quoted && c == '\\' && i + 1 < line.size()) {
            char n = line[++i];
            *cur += n == 'n' ? '\n' : n == 't' ? '\t' : n;
        } else if (quoted) {
            if (c == '"')
                quoted = false;
            else
                *cur += c;
        } else if (c == '"') {
            quoted = true;
            if (!cur) cur = "";
        } else if (c == ' ' || c == '\t') {
            if (cur) args.push_back(*cur), cur.reset();
        } else {
            cur = cur.value_or("") + c;
        }
    }
    if (cur) args.push_back(*cur);
    return args;
}

// render 는 실제 결과를 .scn 의 기대 줄 꼴로 — 같은 규칙으로 견주려고.
std::vector<std::string> render(const Result& r) {
    std::vector<std::string> rows;
    for (auto [prefix, text] :
         {std::pair{"> ", r.out}, {"! ", r.err}}) {
        if (text.empty()) continue;
        bool eol = text.back() == '\n';
        for (auto& l : golden::split(
                 eol ? text.substr(0, text.size() - 1) : text, '\n'))
            rows.push_back(prefix + l);
        if (!eol) rows.push_back("%noeol");
    }
    if (r.code) rows.push_back("= " + std::to_string(r.code));
    return rows;
}

struct Scene {
    std::string root, cwd;
    Env env;

    void date(const std::string& secs) {
        env["GIT_AUTHOR_DATE"] = env["GIT_COMMITTER_DATE"] =
            secs + " +0900";
    }
    std::string gitdir() {
        for (golden::fs::path d = cwd;; d = d.parent_path())
            if (golden::fs::is_directory(d / ".git")) return d / ".git";
    }

    // run 은 한 줄을 돌려 결과. 손질 줄은 nullopt.
    std::optional<Result> run(const std::string& line) {
        auto a = split_args(line);
        auto path = a.size() > 1 ? cwd + "/" + a[1] : "";
        if (a[0] == "@date") {
            date(a[1]);
        } else if (a[0] == "@cd") {
            cwd =
                golden::fs::path(root + "/" + a[1]).lexically_normal();
            if (cwd.back() == '/') cwd.pop_back();
        } else if (a[0] == "write" || a[0] == "append") {
            golden::fs::create_directories(
                golden::fs::path(path).parent_path());
            std::ofstream(
                path,
                std::ios::binary | (a[0] == "append" ? std::ios::app
                                                     : std::ios::trunc))
                << golden::make(a[2]);
        } else if (a[0] == "chmod") {
            ::chmod(path.c_str(), std::stoi(a[2], nullptr, 8));
        } else if (a[0] == "rm") {
            golden::fs::remove(path);
        } else if (a[0] == "mkdir") {
            golden::fs::create_directories(path);
        } else if (a[0] == "mygit") {
            std::vector<std::string> args;
            for (size_t i = 1; i < a.size(); ++i) {
                auto x = a[i];
                for (size_t k; (k = x.find("<ROOT>")) != x.npos;)
                    x.replace(k, 6, root);
                args.push_back(x);
            }
            return mygit::run(args, cwd, env, "");
        } else if (a[0] == "cat") {
            return Result{0, golden::read_file(path), ""};
        } else if (a[0] == "stage") {
            std::string rows;
            for (auto& e : read_index(gitdir())) {
                char m[8];
                std::snprintf(m, sizeof m, "%06o", e.mode);
                rows += std::string(m) + " " + e.oid + " " +
                        std::to_string(e.stage) + "\t" +
                        quote_path(e.path) + "\n";
            }
            return Result{0, rows, ""};
        } else if (a[0] == "ref") {
            return Result{0, rev_parse(gitdir(), a[1]) + "\n", ""};
        } else {
            throw std::runtime_error("모르는 장면 줄: " + line);
        }
        return std::nullopt;
    }
};

void play(const std::string& name) {
    if (STEP < step_of(name))
        throw check::Skip{std::to_string(step_of(name)) +
                          "단계에서 켜진다"};
    golden::TempDir t;
    Scene sc{t.path + "/scene", t.path + "/scene", os_env()};
    golden::fs::create_directories(sc.root);
    for (auto& [k, v] : golden::ident_env()) sc.env[k] = v;
    sc.env["GIT_CEILING_DIRECTORIES"] = t.path;
    sc.date("1700000000");
    // .scn → (명령 줄, 기대 줄들). 기대 줄은 '> ' · '! ' · '= ' 또는
    // '%noeol' 로 시작한다.
    std::vector<std::pair<std::string, std::vector<std::string>>> steps;
    for (auto& line :
         golden::split(golden::read("scen/" + name + ".scn"), '\n')) {
        if (line.empty() || line[0] == '#') continue;
        auto p = line.substr(0, 2);
        if (p == "> " || p == "! " || p == "= " || line == "%noeol") {
            auto w = line;
            for (size_t k; (k = w.find("<ROOT>")) != w.npos;)
                w.replace(k, 6, sc.root);
            steps.back().second.push_back(w);
        } else {
            steps.push_back({line, {}});
        }
    }
    for (size_t k = 0; k < steps.size(); ++k) {
        auto got = sc.run(steps[k].first);
        auto rows = got ? render(*got) : std::vector<std::string>{};
        if (rows != steps[k].second) {
            std::string msg = name + " 장면 " + std::to_string(k) +
                              "번째 줄: " + steps[k].first + "\n얻음:";
            for (auto& r : rows) msg += "\n  " + r;
            msg += "\n기대:";
            for (auto& r : steps[k].second) msg += "\n  " + r;
            throw std::runtime_error(msg);
        }
    }
}
}  // namespace

// 장면마다 시험 하나 — golden/scen 의 파일 목록을 그대로 따른다
#define SCENE(id, name) \
    TEST(s16_4_##id) {  \
        play(name);     \
    }
SCENE(plumbing, "plumbing")
SCENE(status, "status")
SCENE(hello, "hello")
SCENE(diff, "diff")
SCENE(checkout, "checkout")
SCENE(errors, "errors")
SCENE(clone, "clone")
SCENE(merge_add_add, "merge-add-add")
SCENE(merge_adjacent, "merge-adjacent")
SCENE(merge_clean_far, "merge-clean-far")
SCENE(merge_conflict, "merge-conflict")
SCENE(merge_delete, "merge-delete")
SCENE(merge_ff, "merge-ff")
SCENE(merge_identical, "merge-identical")
SCENE(merge_into_dev, "merge-into-dev")
SCENE(merge_join_3, "merge-join-3")
SCENE(merge_one_apart, "merge-one-apart")
SCENE(merge_other_file, "merge-other-file")
SCENE(merge_refine, "merge-refine")
SCENE(merge_resolve, "merge-resolve")
SCENE(merge_split_4, "merge-split-4")

TEST(s16_4_every_scene_file_is_listed) {
    // 새 장면이 golden 에 생기면 위 목록에 한 줄 더해야 한다
    CHECK_EQ(
        std::distance(golden::fs::directory_iterator("golden/scen"),
                      golden::fs::directory_iterator{}),
        21);
}
