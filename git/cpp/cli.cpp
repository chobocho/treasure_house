// 명령줄 (SPEC.md §1 · §9) — 인자를 읽고, 모듈을 부르고, 찍는다.
//
// 출력은 이 파일만 한다. 다른 파일은 값을 돌려주거나 GitError 를
// 던질 뿐이다. run() 은 과정 안에서 부를 수 있는 꼴(코드, 표준 출력,
// 표준 오류)이고, main.cpp 는 그것을 진짜 표준 스트림에 잇는다.
// 명령은 commands() 표에 이름으로 붙는다. 단계가 늘 때마다 한 줄씩.
#include <unistd.h>

#include <cerrno>
#include <cstdio>
#include <cstring>
#include <filesystem>
#include <functional>
#include <iostream>
#include <iterator>
#include <set>
#include <sstream>

#include "mygit.hpp"

extern char** environ;
namespace fs = std::filesystem;

namespace mygit {
namespace {
const std::string not_a_repo =
    "fatal: not a git repository (or any of the parent directories): "
    ".git";

// Ctx 는 명령 하나가 도는 동안의 문맥 — 현재 디렉터리·환경·입출력.
struct Ctx {
    std::string cwd;
    Env env;
    std::optional<std::string> input;
    std::string out, err, root_;

    // stdin 은 필요한 명령(--stdin)만 읽는다 — 늘 읽으면 닫히지 않은
    // 파이프에서 멈춘다.
    const std::string& read_stdin() {
        if (!input)
            input = std::string(
                std::istreambuf_iterator<char>(std::cin), {});
        return *input;
    }

    // root 는 .git 을 품은 디렉터리(SPEC.md §1.1). 현재 디렉터리부터
    // 위로 올라가되 GIT_CEILING_DIRECTORIES 안으로는 올라가지 않는다.
    const std::string& root() {
        if (!root_.empty()) return root_;
        std::set<std::string> ceil;
        std::stringstream spec(env["GIT_CEILING_DIRECTORIES"]);
        for (std::string p; std::getline(spec, p, ':');)
            if (!p.empty())
                ceil.insert(fs::absolute(p).lexically_normal());
        for (fs::path d = cwd;;) {
            if (fs::is_directory(d / ".git")) return root_ = d.string();
            auto up = d.parent_path();
            if (up == d || ceil.count(up.string()))
                throw GitError(not_a_repo);
            d = up;
        }
    }
    std::string gitdir() { return root() + "/.git"; }
    std::string path(const std::string& name) const {
        return name.starts_with("/") ? name : cwd + "/" + name;
    }
};

using Command = std::function<int(Ctx&, std::vector<std::string>)>;

// Flags 는 parse_flags 의 결과 — 켜진 옵션, 값 옵션, 나머지 인자.
struct Flags {
    std::set<std::string> on;
    std::map<std::string, std::string> vals;
    std::vector<std::string> rest;
};

// parse_flags 는 모르는 옵션을 SPEC.md §1.4 의 "unknown option"
// 오류로 거절한다. '--' 뒤는 전부 인자로 본다.
Flags parse_flags(const std::vector<std::string>& args,
                  const std::set<std::string>& on,
                  const std::set<std::string>& valued = {}) {
    Flags f;
    for (size_t i = 0; i < args.size(); ++i) {
        const auto& a = args[i];
        if (a == "--") {
            f.rest.insert(f.rest.end(), args.begin() + i + 1,
                          args.end());
            break;
        }
        if (valued.count(a)) {
            if (i + 1 == args.size())
                throw GitError("fatal: mygit: option '" + a +
                               "' needs a value");
            f.vals[a] = args[++i];
        } else if (on.count(a)) {
            f.on.insert(a);
        } else if (a.size() > 1 && a[0] == '-') {
            throw GitError("fatal: mygit: unknown option '" + a + "'");
        } else {
            f.rest.push_back(a);
        }
    }
    return f;
}

// resolve 는 <rev> → 객체 이름. 없으면 "" (SPEC.md §6.2).
std::string resolve(Ctx& ctx, const std::string& name) {
    return find_object(ctx.gitdir(), name);
}

// ── 3단계: hash-object · cat-file ──────────────────────────────────
int cmd_hash_object(Ctx& ctx, std::vector<std::string> args) {
    auto f = parse_flags(args, {"-w", "--stdin"}, {"-t"});
    std::string type = f.vals.count("-t") ? f.vals["-t"] : "blob";
    if (!is_type(type))
        throw GitError("fatal: mygit: unknown object type '" + type +
                       "'");
    std::vector<std::string> bodies;
    if (f.on.count("--stdin")) {
        bodies.push_back(ctx.read_stdin());
    } else {
        for (auto& name : f.rest) {
            errno = 0;
            auto body = try_read(ctx.path(name));
            if (!body)
                throw GitError(
                    "fatal: could not open '" + name +
                    "' for reading: " + std::strerror(errno));
            bodies.push_back(*body);
        }
    }
    for (auto& body : bodies)
        ctx.out +=
            (f.on.count("-w") ? write_object(ctx.gitdir(), type, body)
                              : hash_object(type, body)) +
            "\n";
    return 0;
}

// pretty 는 cat-file -p 의 몸. blob·commit·tag 는 그대로, 트리는
// 항목마다 "%06o 형식 이름\t경로" (SPEC.md §9, 따옴표는 §8.2).
std::string pretty(const Object& o) {
    if (o.type != "tree") return o.body;
    std::string out;
    for (auto& e : parse_tree(o.body)) {
        char mode[8];
        std::snprintf(mode, sizeof mode, "%06o",
                      unsigned(std::stoul(e.mode, nullptr, 8)));
        out += std::string(mode) + " " + type_of_mode(e.mode) + " " +
               e.oid + "\t" + quote_path(e.name) + "\n";
    }
    return out;
}

int cmd_cat_file(Ctx& ctx, std::vector<std::string> args) {
    auto f = parse_flags(args, {"-t", "-s", "-p"});
    if (f.on.size() != 1 || f.rest.size() != 1)
        throw GitError("usage: mygit cat-file (-t | -s | -p) <object>",
                       129);
    auto oid = resolve(ctx, f.rest[0]);
    if (oid.empty())
        throw GitError("fatal: Not a valid object name " + f.rest[0]);
    auto o = read_object(ctx.gitdir(), oid);
    if (f.on.count("-t"))
        ctx.out += o.type + "\n";
    else if (f.on.count("-s"))
        ctx.out += std::to_string(o.body.size()) + "\n";
    else
        ctx.out += pretty(o);
    return 0;
}

const std::map<std::string, Command>& commands() {
    static const std::map<std::string, Command> table = {
        {"hash-object", cmd_hash_object},
        {"cat-file", cmd_cat_file},
    };
    return table;
}
}  // namespace

// ── 틀 ─────────────────────────────────────────────────────────────
Env os_env() {
    Env env;
    for (char** e = environ; *e; ++e) {
        std::string kv = *e;
        auto eq = kv.find('=');
        if (eq != kv.npos) env[kv.substr(0, eq)] = kv.substr(eq + 1);
    }
    return env;
}

Result run(const std::vector<std::string>& args, const std::string& cwd,
           const Env& env, std::optional<std::string> input) {
    Ctx ctx;
    auto dir =
        fs::absolute(cwd.empty() ? fs::current_path() : fs::path(cwd));
    ctx.cwd = dir.lexically_normal().string();
    if (ctx.cwd.size() > 1 && ctx.cwd.back() == '/') ctx.cwd.pop_back();
    ctx.env = env;
    ctx.input = std::move(input);
    if (args.empty())
        return {129, "", "usage: mygit <command> [<args>]\n"};
    auto it = commands().find(args[0]);
    if (it == commands().end())
        return {1, "",
                "mygit: '" + args[0] + "' is not a mygit command.\n"};
    int code;
    try {
        code = it->second(ctx, {args.begin() + 1, args.end()});
    } catch (const GitError& e) {
        ctx.err += std::string(e.what()) + "\n";
        code = e.code;
    } catch (const fs::filesystem_error& e) {
        // 파일 시스템의 뜻밖의 오류 — git 처럼 fatal 128
        ctx.err += std::string("fatal: ") + e.what() + "\n";
        code = 128;
    }
    return {code, ctx.out, ctx.err};
}
}  // namespace mygit
