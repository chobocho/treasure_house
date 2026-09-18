// 명령줄 (SPEC.md §1 · §9) — 인자를 읽고, 모듈을 부르고, 찍는다.
//
// 출력은 이 파일만 한다. 다른 파일은 값을 돌려주거나 GitError 를
// 던질 뿐이다. run() 은 과정 안에서 부를 수 있는 꼴(코드, 표준 출력,
// 표준 오류)이고, main.cpp 는 그것을 진짜 표준 스트림에 잇는다.
// 명령은 commands() 표에 이름으로 붙는다. 단계가 늘 때마다 한 줄씩.
#include <unistd.h>

#include <algorithm>
#include <cerrno>
#include <cstdio>
#include <cstring>
#include <filesystem>
#include <fstream>
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
    return rev_parse(ctx.gitdir(), name);
}

std::string ambiguous(const std::string& name) {
    return "fatal: ambiguous argument '" + name +
           "': unknown revision or path not in the working tree.\n"
           "Use '--' to separate paths from revisions, like this:\n"
           "'git <command> [<revision>...] -- [<file>...]'";
}

std::string ident(Ctx& ctx, const std::string& who = "COMMITTER") {
    return ident_from_env(ctx.env, who);
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

// ── 5단계: init · commit-tree · branch · tag · reflog ─────────────
const std::string config =
    "[core]\n\trepositoryformatversion = 0\n\tfilemode = true\n"
    "\tbare = false\n\tlogallrefupdates = true\n";

// make_repo 는 top/.git 을 SPEC.md §5.1 의 꼴로. → 이미 있었나.
// 이미 있으면 아무것도 덮어쓰지 않는다.
bool make_repo(const std::string& top) {
    auto g = top + "/.git";
    bool again = fs::is_directory(g);
    for (auto d : {"objects/pack", "refs/heads", "refs/tags"})
        fs::create_directories(g + "/" + d);
    for (auto [name, text] :
         {std::pair{"HEAD", std::string("ref: refs/heads/main\n")},
          std::pair{"config", config}})
        if (!fs::exists(g + "/" + name))
            std::ofstream(g + "/" + name, std::ios::binary) << text;
    return again;
}

int cmd_init(Ctx& ctx, std::vector<std::string> args) {
    auto f = parse_flags(args, {});
    auto top = f.rest.empty() ? ctx.cwd : ctx.path(f.rest[0]);
    bool again = make_repo(top);
    ctx.out += std::string(again ? "Reinitialized existing"
                                 : "Initialized empty") +
               " Git repository in " + top + "/.git/\n";
    return 0;
}

// cmd_commit_tree — -p 와 -m 은 몇 번이든, 준 차례대로. 메시지는 원문
// 그대로 + 줄바꿈 — 공백 정리는 commit 명령만 한다(SPEC.md §4.4).
int cmd_commit_tree(Ctx& ctx, std::vector<std::string> args) {
    std::string tree;
    Commit c;
    std::vector<std::string> msgs;
    for (size_t i = 0; i < args.size(); ++i) {
        const auto& a = args[i];
        if (a == "-p" || a == "-m") {
            if (i + 1 == args.size())
                throw GitError("fatal: mygit: option '" + a +
                               "' needs a value");
            const auto& v = args[++i];
            if (a == "-m") {
                msgs.push_back(v);
                continue;
            }
            auto oid = resolve(ctx, v);
            if (oid.empty())
                throw GitError("fatal: not a valid object name " + v);
            c.parents.push_back(oid);
        } else if (a.starts_with("-")) {
            throw GitError("fatal: mygit: unknown option '" + a + "'");
        } else {
            tree = a;
        }
    }
    if (tree.empty() || msgs.empty())
        throw GitError(
            "usage: mygit commit-tree <tree> "
            "[-p <parent>]... -m <message>...",
            129);
    auto oid = resolve(ctx, tree);
    c.tree = oid.empty() ? "" : peel(ctx.gitdir(), oid, "tree");
    if (c.tree.empty())
        throw GitError("fatal: not a valid object name " + tree);
    for (auto& m : msgs)
        c.message += (c.message.empty() ? "" : "\n\n") + m;
    c.message += "\n";
    c.author = ident(ctx, "AUTHOR");
    c.committer = ident(ctx);
    ctx.out +=
        write_object(ctx.gitdir(), "commit", serialize_commit(c)) +
        "\n";
    return 0;
}

int list_branches(Ctx& ctx) {
    auto [cur, head] = read_head(ctx.gitdir());
    if (cur.empty() && !head.empty())
        ctx.out += "* (HEAD detached at " + head.substr(0, 7) + ")\n";
    for (auto& r : list_refs(ctx.gitdir(), "refs/heads/"))
        ctx.out +=
            (r.name == cur ? "* " : "  ") + r.name.substr(11) + "\n";
    return 0;
}

// delete_branch 는 branch -d — HEAD 에서 닿는 브랜치만 지운다(§9.2).
int delete_branch(Ctx& ctx, const std::vector<std::string>& names) {
    auto g = ctx.gitdir();
    auto [cur, head] = read_head(g);
    for (auto& name : names) {
        auto ref = "refs/heads/" + name;
        auto oid = resolve_ref(g, ref);
        if (ref == cur)
            throw GitError("error: cannot delete branch '" + name +
                               "' used by worktree at '" + ctx.root() +
                               "'",
                           1);
        if (oid.empty())
            throw GitError("error: branch '" + name + "' not found.",
                           1);
        if (head.empty() || !is_ancestor(g, oid, head))
            throw GitError(
                "error: the branch '" + name + "' is not fully merged",
                1);
        update_ref(g, ref, "", oid, "", "");
        ctx.out += "Deleted branch " + name + " (was " +
                   oid.substr(0, 7) + ").\n";
    }
    return 0;
}

int cmd_branch(Ctx& ctx, std::vector<std::string> args) {
    auto f = parse_flags(args, {"-d"});
    if (f.on.count("-d")) return delete_branch(ctx, f.rest);
    if (f.rest.empty()) return list_branches(ctx);
    auto g = ctx.gitdir();
    const auto& name = f.rest[0];
    if (!valid_branch_name(name))
        throw GitError("fatal: '" + name +
                       "' is not a valid branch name");
    if (!resolve_ref(g, "refs/heads/" + name).empty())
        throw GitError("fatal: a branch named '" + name +
                       "' already exists");
    auto start = f.rest.size() > 1 ? f.rest[1] : "HEAD";
    auto oid = resolve(ctx, start);
    if (!oid.empty()) oid = peel(g, oid, "commit");
    if (oid.empty())
        throw GitError("fatal: not a valid object name: '" + start +
                       "'");
    update_ref(g, "refs/heads/" + name, oid, "",
               "branch: Created from " + start, ident(ctx));
    return 0;
}

int cmd_tag(Ctx& ctx, std::vector<std::string> args) {
    auto f = parse_flags(args, {"-a"}, {"-m"});
    auto g = ctx.gitdir();
    if (f.rest.empty()) {
        for (auto& r : list_refs(g, "refs/tags/"))
            ctx.out += r.name.substr(10) + "\n";
        return 0;
    }
    const auto& name = f.rest[0];
    auto target = f.rest.size() > 1 ? f.rest[1] : "HEAD";
    if (read_ref(g, "refs/tags/" + name))
        throw GitError("fatal: tag '" + name + "' already exists");
    auto oid = resolve(ctx, target);
    if (oid.empty())
        throw GitError("fatal: Failed to resolve '" + target +
                       "' as a valid ref.");
    if (f.on.count("-a") || f.vals.count("-m")) {
        auto type = read_object(g, oid).type;
        auto msg = cleanup_message(f.vals["-m"]);
        oid = write_object(
            g, "tag", serialize_tag(oid, type, name, ident(ctx), msg));
    }
    // 태그는 reflog 를 남기지 않는다 — logallrefupdates 는 브랜치와
    // HEAD 만 기록한다(git 과 같다)
    fs::create_directories(g + "/refs/tags");
    std::ofstream(g + "/refs/tags/" + name, std::ios::binary)
        << oid + "\n";
    return 0;
}

// cmd_reflog 는 새것부터 '<7글자> <ref>@{n}: <메시지>' (SPEC.md §6.3).
int cmd_reflog(Ctx& ctx, std::vector<std::string> args) {
    auto f = parse_flags(args, {});
    std::erase(f.rest, "show");
    auto name = f.rest.empty() ? "HEAD" : f.rest[0];
    std::string log;
    for (auto cand : {name, "refs/heads/" + name})
        if (log.empty() && fs::exists(ctx.gitdir() + "/logs/" + cand))
            log = cand;
    if (log.empty()) {
        if (name == "HEAD") return 0;
        throw GitError(ambiguous(name));
    }
    auto ents = read_reflog(ctx.gitdir(), log);
    for (size_t k = 0; k < ents.size(); ++k)
        ctx.out += ents[ents.size() - 1 - k].now.substr(0, 7) + " " +
                   name + "@{" + std::to_string(k) +
                   "}: " + ents[ents.size() - 1 - k].msg + "\n";
    return 0;
}

// ── 6단계: add · rm --cached · status · write-tree · commit ────────

// rel_path 는 명령줄 경로 → 작업 트리 뿌리에서의 경로('' 은 뿌리).
std::string rel_path(Ctx& ctx, const std::string& spec) {
    auto p = fs::path(ctx.path(spec))
                 .lexically_normal()
                 .lexically_relative(ctx.root())
                 .generic_string();
    if (p.ends_with("/")) p.pop_back();
    return p == "." ? "" : p;
}

bool under(const std::string& path, const std::string& rel) {
    return rel.empty() || path == rel || path.starts_with(rel + "/");
}

// cmd_add 는 pathspec 아래의 파일을 올리고, 사라진 파일은 뺀다(§9).
// 모든 pathspec 을 먼저 검사한다 — 하나라도 맞는 것이 없으면 아무것도
// 바꾸지 않고 멈춘다(git 과 같다).
int cmd_add(Ctx& ctx, std::vector<std::string> args) {
    auto f = parse_flags(args, {});
    auto root = ctx.root(), g = ctx.gitdir();
    auto ents = read_index(g);
    auto files = walk_worktree(root);
    std::vector<
        std::pair<std::vector<std::string>, std::set<std::string>>>
        plan;
    for (auto& spec : f.rest) {
        auto rel = rel_path(ctx, spec);
        std::vector<std::string> hit_f;
        std::set<std::string> hit_i;
        for (auto& p : files)
            if (under(p, rel)) hit_f.push_back(p);
        for (auto& e : ents)
            if (under(e.path, rel)) hit_i.insert(e.path);
        if (hit_f.empty() && hit_i.empty())
            throw GitError("fatal: pathspec '" + spec +
                           "' did not match any files");
        plan.push_back({hit_f, hit_i});
    }
    std::map<std::string, std::vector<IndexEntry>> by_path;
    for (auto& e : ents) by_path[e.path].push_back(e);
    for (auto& [hit_f, hit_i] : plan) {
        for (auto& p : hit_f) {
            auto full = root + "/" + p;
            auto oid = write_object(g, "blob", try_read(full).value());
            by_path[p] = {entry_from_stat(p, full, oid)};
            hit_i.erase(p);
        }
        for (auto& p : hit_i) by_path.erase(p);
    }
    std::vector<IndexEntry> out;
    for (auto& [_, es] : by_path)
        out.insert(out.end(), es.begin(), es.end());
    write_index(g, out);
    return 0;
}

int cmd_rm(Ctx& ctx, std::vector<std::string> args) {
    auto f = parse_flags(args, {"--cached"});
    if (!f.on.count("--cached"))
        throw GitError("fatal: mygit: only rm --cached is supported");
    auto g = ctx.gitdir();
    auto ents = read_index(g);
    std::set<std::string> have, gone;
    for (auto& e : ents) have.insert(e.path);
    for (auto& spec : f.rest) {
        auto rel = rel_path(ctx, spec);
        if (!have.count(rel))
            throw GitError("fatal: pathspec '" + spec +
                           "' did not match any files");
        gone.insert(rel);
    }
    for (auto& p : gone) ctx.out += "rm '" + p + "'\n";
    std::erase_if(ents,
                  [&](auto& e) { return gone.count(e.path) > 0; });
    write_index(g, ents);
    return 0;
}

int cmd_status(Ctx& ctx, std::vector<std::string> args) {
    parse_flags(args, {"--porcelain", "-s", "--short"});
    for (auto& row : status(ctx.root(), ctx.gitdir()))
        ctx.out += row + "\n";
    return 0;
}

// index_tree 는 인덱스(단계 0) → 트리 이름. 충돌 경로가 있으면 쓸 수
// 없다.
std::string index_tree(Ctx& ctx) {
    std::vector<PathEntry> pes;
    for (auto& e : read_index(ctx.gitdir())) {
        if (e.stage)
            throw GitError(
                "error: Committing is not possible because you have "
                "unmerged files.\nfatal: Exiting because of an "
                "unresolved "
                "conflict.");
        char mode[8];
        std::snprintf(mode, sizeof mode, "%o", e.mode);
        pes.push_back({mode, e.oid, e.path});
    }
    return write_tree(ctx.gitdir(), pes);
}

int cmd_write_tree(Ctx& ctx, std::vector<std::string> args) {
    parse_flags(args, {});
    ctx.out += index_tree(ctx) + "\n";
    return 0;
}

// cmd_commit 은 트리를 쓰고, 커밋하고, 브랜치를 옮긴다(SPEC.md §9 ·
// §6.3). 부모는 HEAD 와, 머지를 마무리하는 중이면 MERGE_HEAD. 출력은
// git 의 요약 첫 줄만 — Author 줄과 변경 통계는 줄임이다.
int cmd_commit(Ctx& ctx, std::vector<std::string> args) {
    std::vector<std::string> msgs;
    for (size_t i = 0; i < args.size(); ++i) {
        if (args[i] != "-m")
            throw GitError("fatal: mygit: unknown option '" + args[i] +
                           "'");
        msgs.push_back(i + 1 < args.size() ? args[++i] : "");
    }
    auto g = ctx.gitdir();
    auto [branch, head] = read_head(g);
    auto merge_head = resolve_ref(g, "MERGE_HEAD");
    auto t = index_tree(ctx);
    if (!head.empty() && merge_head.empty() &&
        peel(g, head, "tree") == t) {
        ctx.out += "nothing to commit\n";
        return 1;
    }
    std::string joined;
    for (auto& m : msgs) joined += (joined.empty() ? "" : "\n\n") + m;
    Commit c{t,
             {},
             ident(ctx, "AUTHOR"),
             ident(ctx),
             cleanup_message(joined)};
    if (c.message.empty())
        throw GitError("Aborting commit due to empty commit message.",
                       1);
    for (auto& p : {head, merge_head})
        if (!p.empty()) c.parents.push_back(p);
    auto oid = write_object(g, "commit", serialize_commit(c));
    auto subj = subject_of(c.message);
    auto kind = head.empty()         ? "commit (initial)"
                : merge_head.empty() ? "commit"
                                     : "commit (merge)";
    update_ref(g, branch.empty() ? "HEAD" : branch, oid, head,
               std::string(kind) + ": " + subj, c.committer);
    fs::remove(g + "/MERGE_HEAD"), fs::remove(g + "/MERGE_MSG");
    ctx.out += "[" +
               (branch.empty() ? "detached HEAD" : branch.substr(11)) +
               (head.empty() ? " (root-commit)" : "") + " " +
               oid.substr(0, 7) + "] " + subj + "\n";
    return 0;
}

// ── 7단계: log · merge-base ─────────────────────────────────────────

// log_entry 는 커밋 하나를 git log 의 꼴로(SPEC.md §9.1).
std::string log_entry(Ctx& ctx, const std::string& oid, bool oneline) {
    auto c = parse_commit(read_object(ctx.gitdir(), oid).body);
    if (oneline)
        return oid.substr(0, 7) + " " + subject_of(c.message) + "\n";
    auto who = parse_ident(c.author);
    std::string s = "commit " + oid + "\n";
    if (c.parents.size() > 1) {
        s += "Merge:";
        for (auto& p : c.parents) s += " " + p.substr(0, 7);
        s += "\n";
    }
    s += "Author: " + who.name + " <" + who.mail +
         ">\nDate:   " + format_date(who.secs, who.tz) + "\n\n";
    auto msg = c.message;
    if (msg.ends_with("\n")) msg.pop_back();
    size_t a = 0;
    for (size_t b; (b = msg.find('\n', a)) != msg.npos; a = b + 1)
        s += "    " + msg.substr(a, b - a) + "\n";
    return s + "    " + msg.substr(a) + "\n";
}

int cmd_log(Ctx& ctx, std::vector<std::string> args) {
    auto f = parse_flags(args, {"--oneline"}, {"-n"});
    auto g = ctx.gitdir();
    std::string start;
    if (!f.rest.empty()) {
        start = resolve(ctx, f.rest[0]);
        if (!start.empty()) start = peel(g, start, "commit");
        if (start.empty()) throw GitError(ambiguous(f.rest[0]));
    } else {
        auto [branch, head] = read_head(g);
        if (head.empty())
            throw GitError("fatal: your current branch '" +
                           branch.substr(11) +
                           "' does not have any commits yet");
        start = head;
    }
    auto order = walk_log(g, {start});
    if (f.vals.count("-n"))
        order.resize(std::min(order.size(), std::stoul(f.vals["-n"])));
    bool one = f.on.count("--oneline");
    for (size_t k = 0; k < order.size(); ++k)
        ctx.out +=
            (k && !one ? "\n" : "") + log_entry(ctx, order[k], one);
    return 0;
}

int cmd_merge_base(Ctx& ctx, std::vector<std::string> args) {
    auto f = parse_flags(args, {"--all"});
    if (f.rest.size() != 2)
        throw GitError("usage: mygit merge-base [--all] <a> <b>", 129);
    auto g = ctx.gitdir();
    std::vector<std::string> ids;
    for (auto& name : f.rest) {
        auto oid = resolve(ctx, name);
        if (!oid.empty()) oid = peel(g, oid, "commit");
        if (oid.empty())
            throw GitError("fatal: Not a valid object name " + name);
        ids.push_back(oid);
    }
    auto best = merge_bases(g, ids[0], ids[1]);
    if (best.empty()) return 1;
    if (!f.on.count("--all")) best.resize(1);
    for (auto& oid : best) ctx.out += oid + "\n";
    return 0;
}

// ── 8단계: diff ─────────────────────────────────────────────────────

// rev_tree_map 은 <rev> 의 트리를 펼쳐 {경로: Blob}.
TreeMap rev_tree_map(Ctx& ctx, const std::string& rev) {
    auto oid = resolve(ctx, rev);
    auto t = oid.empty() ? "" : peel(ctx.gitdir(), oid, "tree");
    if (t.empty()) throw GitError(ambiguous(rev));
    return tree_map(ctx.gitdir(), t);
}

// cmd_diff 는 SPEC.md §11.5 의 네 꼴. --no-index 만 다르면 1 로 끝난다.
int cmd_diff(Ctx& ctx, std::vector<std::string> args) {
    auto f = parse_flags(args, {"--cached", "--no-index"});
    if (f.on.count("--no-index")) {
        if (f.rest.size() != 2)
            throw GitError("usage: mygit diff --no-index <a> <b>", 129);
        auto text = file_diff(f.rest[0], f.rest[1],
                              disk_side(ctx.path(f.rest[0])),
                              disk_side(ctx.path(f.rest[1])));
        ctx.out += text;
        return text.empty() ? 0 : 1;
    }
    auto g = ctx.gitdir(), root = ctx.root();
    TreeMap a, b;
    bool disk = false;  // 새 쪽이 작업 트리인가
    if (f.rest.size() == 2) {
        a = rev_tree_map(ctx, f.rest[0]),
        b = rev_tree_map(ctx, f.rest[1]);
    } else if (!f.rest.empty()) {
        throw GitError(ambiguous(f.rest[0]));
    } else {
        std::set<std::string> conflicted;
        for (auto& e : read_index(g))
            if (e.stage)
                conflicted.insert(e.path);
            else
                b[e.path] = {e.mode, e.oid};
        if (f.on.count("--cached")) {
            a = tree_map(g, head_tree(g));
        } else {
            // 작업 트리 ↔ 인덱스: 충돌 경로는 건너뛴다(줄임)
            a.swap(b), disk = true;
            for (auto& p : conflicted) a.erase(p);
            for (auto& [p, _] : a)
                if (auto s = disk_side(root + "/" + p))
                    b[p] = {s->mode, s->oid};
        }
    }
    std::set<std::string> all;
    for (auto& [p, _] : a) all.insert(p);
    for (auto& [p, _] : b) all.insert(p);
    for (auto& p : all) {
        auto oa = a.find(p), ob = b.find(p);
        bool ina = oa != a.end(), inb = ob != b.end();
        if (ina == inb && (!ina || oa->second == ob->second)) continue;
        std::optional<Side> old, now;
        if (ina) old = blob_side(g, oa->second);
        if (inb)
            now = disk ? disk_side(root + "/" + p)
                       : blob_side(g, ob->second);
        ctx.out += file_diff(p, p, old, now);
    }
    return 0;
}

// ── 9단계: switch · checkout ─────────────────────────────────────────

// summary_line 은 '<7글자> <제목>' — HEAD is now at … 의 꼬리.
std::string summary_line(Ctx& ctx, const std::string& oid) {
    auto msg =
        parse_commit(read_object(ctx.gitdir(), oid).body).message;
    return oid.substr(0, 7) + " " + subject_of(msg);
}

// move_head 는 작업 트리를 oid 로 옮기고 HEAD 를 branch(또는 "" 이면
// 분리)로(SPEC.md §9.3). 안내는 표준 오류에, 남은 변경 알림은 표준
// 출력에. reflog 는 "checkout: moving from <옛> to <arg 그대로>" —
// 옛 쪽이 분리 상태면 40글자다(§6.3). done 은 마지막 안내 줄.
int move_head(Ctx& ctx, const std::string& branch,
              const std::string& oid, const std::string& arg,
              bool report = true, std::string done = "") {
    auto g = ctx.gitdir();
    auto [old_branch, old] = read_head(g);
    auto old_tree = old.empty() ? "" : peel(g, old, "tree");
    auto new_tree = peel(g, oid, "tree");
    checkout_tree(ctx.root(), g, old_tree, new_tree);
    // 분리 상태를 떠나되 커밋이 바뀔 때만 — 같은 커밋이면 git 도
    // 찍지 않는다
    if (old_branch.empty() && !old.empty() && oid != old)
        ctx.err += "Previous HEAD position was " +
                   summary_line(ctx, old) + "\n";
    set_head(g, branch.empty() ? oid : branch);
    auto from = old_branch.empty() ? old : old_branch.substr(11);
    append_reflog(g, "HEAD", old, oid, ident(ctx),
                  "checkout: moving from " + from + " to " + arg);
    if (report)
        for (auto& row : local_changes(ctx.root(), g, new_tree))
            ctx.out += row + "\n";
    if (done.empty())
        done =
            branch.empty() ? "HEAD is now at " + summary_line(ctx, oid)
            : branch == old_branch ? "Already on '" + arg + "'"
                                   : "Switched to branch '" + arg + "'";
    ctx.err += done + "\n";
    return 0;
}

int create_and_switch(Ctx& ctx, const std::string& name,
                      const std::string& start) {
    auto g = ctx.gitdir();
    if (!valid_branch_name(name))
        throw GitError("fatal: '" + name +
                       "' is not a valid branch name");
    if (!resolve_ref(g, "refs/heads/" + name).empty())
        throw GitError("fatal: a branch named '" + name +
                       "' already exists");
    auto old = read_head(g).second;
    auto fresh = "Switched to a new branch '" + name + "'";
    if (old.empty() && start.empty()) {
        // 첫 커밋 전 — HEAD 가 가리키는 이름만 바꾼다
        set_head(g, "refs/heads/" + name);
        ctx.err += fresh + "\n";
        return 0;
    }
    auto arg = start.empty() ? "HEAD" : start;
    auto oid = resolve(ctx, arg);
    if (!oid.empty()) oid = peel(g, oid, "commit");
    if (oid.empty()) throw GitError("fatal: invalid reference: " + arg);
    update_ref(g, "refs/heads/" + name, oid, "",
               "branch: Created from " + arg, ident(ctx));
    // 지금 커밋에서 새 브랜치를 만들 때는 git 이 작업 트리를 건드리지
    // 않고 남은 변경도 알리지 않는다(golden/scen/checkout.scn)
    return move_head(ctx, "refs/heads/" + name, oid, name, oid != old,
                     fresh);
}

int cmd_switch(Ctx& ctx, std::vector<std::string> args) {
    auto f = parse_flags(args, {}, {"-c"});
    if (f.vals.count("-c"))
        return create_and_switch(ctx, f.vals["-c"],
                                 f.rest.empty() ? "" : f.rest[0]);
    if (f.rest.size() != 1)
        throw GitError("usage: mygit switch [-c] <branch>", 129);
    const auto& name = f.rest[0];
    auto oid = resolve_ref(ctx.gitdir(), "refs/heads/" + name);
    if (!oid.empty())
        return move_head(ctx, "refs/heads/" + name, oid, name);
    if (!resolve(ctx, name).empty())
        throw GitError("fatal: a branch is expected, got commit '" +
                       name + "'");
    throw GitError("fatal: invalid reference: " + name);
}

int cmd_checkout(Ctx& ctx, std::vector<std::string> args) {
    auto f = parse_flags(args, {});
    if (f.rest.size() != 1)
        throw GitError("usage: mygit checkout <branch|commit>", 129);
    const auto& name = f.rest[0];
    auto oid = resolve_ref(ctx.gitdir(), "refs/heads/" + name);
    if (!oid.empty())
        return move_head(ctx, "refs/heads/" + name, oid, name);
    oid = resolve(ctx, name);
    if (!oid.empty()) oid = peel(ctx.gitdir(), oid, "commit");
    if (oid.empty())
        throw GitError("error: pathspec '" + name +
                           "' did not match any file(s) known to git",
                       1);
    return move_head(ctx, "", oid, name);
}

// ── 10단계: merge ────────────────────────────────────────────────────
const std::string mygit_merge =
    "Merge made by mygit (3-way, no renames).";

void write_git_file(Ctx& ctx, const std::string& name,
                    const std::string& text) {
    std::ofstream(ctx.gitdir() + "/" + name, std::ios::binary) << text;
}

// is_clean 은 인덱스가 HEAD 트리와 같고 추적 파일이 그대로인가
// (SPEC.md §12.1).
bool is_clean(Ctx& ctx, const std::string& head) {
    auto g = ctx.gitdir();
    auto want = tree_map(g, peel(g, head, "tree"));
    TreeMap have;
    for (auto& e : read_index(g)) {
        if (e.stage) return false;
        have[e.path] = {e.mode, e.oid};
    }
    if (have != want) return false;
    for (auto& [p, v] : have)
        if (file_state(ctx.root(), p) != v) return false;
    return true;
}

// apply_merge 는 합친 결과를 작업 트리와 인덱스에 쓴다. 충돌 경로는
// 단계 1‥3.
void apply_merge(Ctx& ctx, const TreeMap& ours, const TreeMerge& tm) {
    auto g = ctx.gitdir(), root = ctx.root();
    std::map<std::string, IndexEntry> ents;
    for (auto& e : read_index(g)) ents[e.path] = e;
    std::vector<IndexEntry> staged;
    for (auto& [p, r] : tm.result) {
        auto old = ours.find(p);
        if (r.gone) {
            if (old != ours.end()) remove_file(root, p);
            ents.erase(p);
        } else if (r.conflict) {
            write_file(root, p, r.blob.mode, r.text);
            ents.erase(p);
            for (auto& [k, b] : r.stages)
                staged.push_back(index_entry(p, b.oid, b.mode, k));
        } else if (old == ours.end() || old->second != r.blob) {
            write_file(root, p, r.blob.mode,
                       read_object(g, r.blob.oid).body);
            ents[p] = entry_from_stat(p, root + "/" + p, r.blob.oid);
        }
    }
    for (auto& [_, e] : ents) staged.push_back(e);
    write_index(g, staged);
}

// cmd_merge 는 SPEC.md §12.1 — 이미 최신 · fast-forward · 3-way.
int cmd_merge(Ctx& ctx, std::vector<std::string> args) {
    auto f = parse_flags(args, {});
    if (f.rest.size() != 1)
        throw GitError("usage: mygit merge <branch>", 129);
    auto g = ctx.gitdir();
    const auto& name = f.rest[0];
    auto theirs = resolve(ctx, name);
    if (!theirs.empty()) theirs = peel(g, theirs, "commit");
    if (theirs.empty())
        throw GitError(
            "merge: " + name + " - not something we can merge", 1);
    auto [branch, head] = read_head(g);
    if (head.empty())  // git 은 <b> 를 그대로 가져온다 — 줄임
        throw GitError("fatal: mygit: nothing to merge into yet");
    if (!is_clean(ctx, head))
        throw GitError(
            "error: mygit: commit your local changes before merging");
    auto target = branch.empty() ? "HEAD" : branch;
    // git 은 이미 최신이어도 ORIG_HEAD 를 지금 HEAD 로 다시 쓴다
    // (golden/scen/merge-ff.scn 의 두 번째 merge 뒤)
    write_git_file(ctx, "ORIG_HEAD", head + "\n");
    if (is_ancestor(g, theirs, head)) {
        ctx.out += "Already up to date.\n";
        return 0;
    }
    if (is_ancestor(g, head, theirs)) {
        ctx.out += "Updating " + head.substr(0, 7) + ".." +
                   theirs.substr(0, 7) + "\nFast-forward\n";
        checkout_tree(ctx.root(), g, peel(g, head, "tree"),
                      peel(g, theirs, "tree"));
        update_ref(g, target, theirs, head,
                   "merge " + name + ": Fast-forward", ident(ctx));
        return 0;
    }
    auto bases = merge_bases(g, head, theirs);
    if (bases.size() != 1)
        throw GitError("fatal: mygit: " + std::to_string(bases.size()) +
                       " merge bases (criss-cross) are not supported");
    auto tmap = [&](const std::string& c) {
        return tree_map(g, peel(g, c, "tree"));
    };
    auto ours = tmap(head);
    auto tm = merge_trees(g, tmap(bases[0]), ours, tmap(theirs), name);
    apply_merge(ctx, ours, tm);
    for (auto& line : tm.notes) ctx.out += line + "\n";
    bool is_branch = !resolve_ref(g, "refs/heads/" + name).empty();
    auto msg =
        std::string(is_branch ? "Merge branch '" : "Merge commit '") +
        name + "'";
    auto cur = branch.empty() ? "" : branch.substr(11);
    if (!cur.empty() && cur != "main" && cur != "master")
        msg += " into " + cur;
    if (!tm.conflicts.empty()) {
        write_git_file(ctx, "MERGE_HEAD", theirs + "\n");
        auto text = msg + "\n\n# Conflicts:\n";
        for (auto& p : tm.conflicts) text += "#\t" + p + "\n";
        write_git_file(ctx, "MERGE_MSG", text);
        ctx.out +=
            "Automatic merge failed; fix conflicts and then commit "
            "the result.\n";
        return 1;
    }
    Commit c{index_tree(ctx),
             {head, theirs},
             ident(ctx, "AUTHOR"),
             ident(ctx),
             msg + "\n"};
    auto oid = write_object(g, "commit", serialize_commit(c));
    update_ref(g, target, oid, head,
               "merge " + name + ": " + mygit_merge, c.committer);
    ctx.out += mygit_merge + "\n";
    return 0;
}

const std::map<std::string, Command>& commands() {
    static const std::map<std::string, Command> table = {
        {"hash-object", cmd_hash_object},
        {"cat-file", cmd_cat_file},
        {"init", cmd_init},
        {"commit-tree", cmd_commit_tree},
        {"branch", cmd_branch},
        {"tag", cmd_tag},
        {"reflog", cmd_reflog},
        {"add", cmd_add},
        {"rm", cmd_rm},
        {"status", cmd_status},
        {"write-tree", cmd_write_tree},
        {"commit", cmd_commit},
        {"log", cmd_log},
        {"merge-base", cmd_merge_base},
        {"diff", cmd_diff},
        {"switch", cmd_switch},
        {"checkout", cmd_checkout},
        {"merge", cmd_merge},
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
