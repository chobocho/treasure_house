// 시험 도우미 — golden/ 을 읽고 재료를 바이트로 만든다(SPEC §2.1).
// golden 은 진짜 git 이 만든 기준 바이트다. 시험은 git 을 부르지 않고
// 이 파일들만 읽는다. 경로는 git/ 에서 도는 make test-cpp 기준.
#pragma once
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <map>
#include <sstream>
#include <string>
#include <vector>

#include "check.hpp"

namespace golden {
inline const std::string dir = "golden";

inline std::string read(const std::string& rel) {
    std::ifstream f(dir + "/" + rel, std::ios::binary);
    if (!f) throw std::runtime_error("golden 없음: " + rel);
    std::ostringstream s;
    s << f.rdbuf();
    return s.str();
}

inline std::vector<std::string> split(const std::string& s, char sep) {
    std::vector<std::string> out;
    size_t a = 0;
    for (size_t b; (b = s.find(sep, a)) != std::string::npos; a = b + 1)
        out.push_back(s.substr(a, b - a));
    out.push_back(s.substr(a));
    return out;
}

using Row = std::map<std::string, std::string>;

// tsv 는 주석(#)과 머리 줄을 뺀 행들을 칸 이름 → 값으로.
inline std::vector<Row> tsv(const std::string& rel) {
    std::vector<std::string> head;
    std::vector<Row> rows;
    for (auto& line : split(read(rel), '\n')) {
        if (line.empty() || line[0] == '#') continue;
        auto cols = split(line, '\t');
        if (head.empty()) {
            head = cols;
            continue;
        }
        Row r;
        for (size_t i = 0; i < head.size() && i < cols.size(); ++i)
            r[head[i]] = cols[i];
        rows.push_back(r);
    }
    return rows;
}

// unescape 는 text: 재료의 \n \t \\ \" \xHH 를 푼다.
inline std::string unescape(const std::string& s) {
    std::string out;
    for (size_t i = 0; i < s.size(); ++i) {
        if (s[i] != '\\' || i + 1 >= s.size()) {
            out += s[i];
            continue;
        }
        char n = s[++i];
        if (n == 'x') {
            out += char(std::stoi(s.substr(i + 1, 2), nullptr, 16));
            i += 2;
        } else {
            out += n == 'n' ? '\n' : n == 't' ? '\t' : n;
        }
    }
    return out;
}

// make 는 재료 한 줄을 바이트로(SPEC §2.1 · §16.4).
inline std::string make(const std::string& r) {
    auto c = r.find(':');
    std::string kind = r.substr(0, c),
                arg = c == r.npos ? "" : r.substr(c + 1);
    if (kind == "empty") return "";
    if (kind == "text") return unescape(arg);
    if (kind == "repeat") {
        auto p = split(arg, ':');
        return std::string(std::stoul(p[1]),
                           char(std::stoi(p[0], nullptr, 16)));
    }
    if (kind == "counter") {
        std::string out(std::stoul(arg), '\0');
        for (size_t i = 0; i < out.size(); ++i) out[i] = char(i % 251);
        return out;
    }
    if (kind == "seq") {
        auto p = split(arg, ':');
        std::string out;
        for (int i = std::stoi(p[0]); i <= std::stoi(p[1]); ++i)
            out += std::to_string(i) + "\n";
        return out;
    }
    if (kind == "golden") return read(arg);
    throw std::runtime_error("모르는 재료: " + r);
}

// git_error 는 fn 이 진짜 GitError 를 던지는지 — 코드 99(껍데기)는
// 아니다.
template <class F>
mygit::GitError git_error(F fn) {
    try {
        fn();
    } catch (const mygit::GitError& e) {
        if (e.code == 99) throw;
        return e;
    }
    throw std::runtime_error("GitError 가 나지 않았다");
}

namespace fs = std::filesystem;

// TempDir 는 시험 하나의 임시 디렉터리 — 끝나면 통째로 지운다.
struct TempDir {
    std::string path;
    TempDir() {
        std::string t = (fs::temp_directory_path() / "mygit-XXXXXX");
        if (!mkdtemp(t.data())) throw std::runtime_error("mkdtemp");
        path = t;
    }
    ~TempDir() {
        std::error_code ec;
        fs::remove_all(path, ec);
    }
    TempDir(const TempDir&) = delete;
};

inline void write_file(const std::string& p, const std::string& data) {
    fs::create_directories(fs::path(p).parent_path());
    std::ofstream(p, std::ios::binary | std::ios::trunc) << data;
}

inline std::string read_file(const std::string& p) {
    std::ifstream f(p, std::ios::binary);
    std::ostringstream s;
    s << f.rdbuf();
    return s.str();
}

// gitdir 은 빈 .git 뼈대(objects/pack)를 만든다.
inline std::string gitdir(const TempDir& t) {
    auto g = t.path + "/.git";
    fs::create_directories(g + "/objects/pack");
    return g;
}

// plant 는 git 이 쓴 느슨한 객체를 그대로 심는다.
inline void plant(const std::string& g, const std::string& oid) {
    write_file(g + "/objects/" + oid.substr(0, 2) + "/" + oid.substr(2),
               read("objects/" + oid));
}

// row 는 golden/errors.tsv 에서 명령 하나의 (첫 줄, 종료 코드).
inline std::pair<std::string, int> error_row(const std::string& cmd) {
    for (auto& r : tsv("errors.tsv"))
        if (r["command"] == cmd)
            return {r["stderr-first-line"], std::stoi(r["exit"])};
    throw std::runtime_error("errors.tsv 에 없다: " + cmd);
}

inline std::string first_line(const std::string& s) {
    return s.substr(0, s.find('\n'));
}

// Sandbox 는 임시 디렉터리 안의 작업 트리 w. repo 면 .git 뼈대를 손으로
// 만든다(init 은 5단계의 일). 위로 올라가다 이 덱의 저장소를 찾지 않게
// GIT_CEILING_DIRECTORIES 를 둔다(SPEC.md §1.1).
struct Sandbox {
    TempDir t;
    std::string root;
    mygit::Env env;
    explicit Sandbox(bool repo)
        : root(t.path + "/w"), env(mygit::os_env()) {
        fs::create_directories(root);
        if (repo) {
            for (auto d : {"objects/pack", "refs/heads", "refs/tags"})
                fs::create_directories(root + "/.git/" + d);
            write_file(root + "/.git/HEAD", "ref: refs/heads/main\n");
        }
        env["GIT_CEILING_DIRECTORIES"] = t.path;
    }
    mygit::Result run(const std::string& input,
                      std::vector<std::string> args) {
        auto r = mygit::run(args, root, env, input);
        if (r.code == 99) throw mygit::GitError("not implemented", 99);
        return r;
    }
    mygit::Result mygit(std::vector<std::string> args) {
        return run("", std::move(args));
    }
    void put(const std::string& name, const std::string& data) {
        write_file(root + "/" + name, data);
    }
};

inline mygit::Env ident_env() {
    return {{"GIT_AUTHOR_NAME", "A U Thor"},
            {"GIT_AUTHOR_EMAIL", "author@example.com"},
            {"GIT_AUTHOR_DATE", "1700000000 +0900"},
            {"GIT_COMMITTER_NAME", "C O Mitter"},
            {"GIT_COMMITTER_EMAIL", "committer@example.com"},
            {"GIT_COMMITTER_DATE", "1700000000 +0900"}};
}

// copy_tree 는 golden 의 .git 사본을 dst 로 베낀다(시험 준비 전용).
inline void copy_tree(const std::string& src, const std::string& dst) {
    fs::create_directories(dst);
    fs::copy(src, dst, fs::copy_options::recursive);
    for (auto& e : fs::recursive_directory_iterator(dst))
        fs::permissions(e.path(), fs::perms::owner_write,
                        fs::perm_options::add);
}

// dag 는 golden/dag/<역사>/git 을 작업 트리의 .git 으로 베낀 샌드박스.
inline void dag(Sandbox& s, const std::string& name) {
    copy_tree(dir + "/dag/" + name + "/git", s.root + "/.git");
    for (auto d : {"objects/pack", "refs/tags"})
        fs::create_directories(s.root + "/.git/" + d);
    s.env["GIT_COMMITTER_NAME"] = "C O Mitter";
    s.env["GIT_COMMITTER_EMAIL"] = "committer@example.com";
    s.env["GIT_COMMITTER_DATE"] = "1700000000 +0900";
}
}  // namespace golden
