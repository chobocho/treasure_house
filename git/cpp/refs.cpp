// 참조 (SPEC.md §6) — 브랜치는 40글자가 든 파일 하나다.
//
// refs/heads/main 은 커밋 이름 한 줄이고, HEAD 는 보통 "ref: refs/
// heads/main" 이라는 이름표를 가리키는 이름표다. gc 뒤의 저장소는
// 참조를 packed-refs 한 파일에 모아 두므로 읽을 때는 둘 다 본다
// (느슨한 파일이 이긴다). 쓸 때는 느슨한 파일만 쓴다.
#include <fcntl.h>
#include <unistd.h>

#include <algorithm>
#include <filesystem>
#include <fstream>
#include <sstream>

#include "mygit.hpp"

namespace fs = std::filesystem;

namespace mygit {
namespace {
std::string trim(const std::string& s) {
    auto a = s.find_first_not_of(" \t\r\n");
    return a == s.npos
               ? ""
               : s.substr(a, s.find_last_not_of(" \t\r\n") - a + 1);
}

// write_locked 는 <경로>.lock 에 쓰고 이름을 바꿔 넣는다(SPEC.md §6.1).
// O_EXCL 이라 다른 쓰는 이가 있으면 멈춘다.
void write_locked(const std::string& path, const std::string& text) {
    fs::create_directories(fs::path(path).parent_path());
    auto lock = path + ".lock";
    int fd = open(lock.c_str(), O_WRONLY | O_CREAT | O_EXCL, 0666);
    if (fd < 0) throw GitError("fatal: mygit: unable to lock " + path);
    bool ok =
        write(fd, text.data(), text.size()) == ssize_t(text.size());
    if (close(fd) != 0 || !ok ||
        rename(lock.c_str(), path.c_str()) != 0)
        throw GitError("fatal: mygit: cannot write " + path);
}

std::vector<std::string> parents_of(const std::string& gitdir,
                                    const std::string& oid) {
    return parse_commit(read_object(gitdir, oid).body).parents;
}

bool is_hex40(const std::string& s) {
    return s.size() == 40 &&
           s.find_first_not_of("0123456789abcdef") == s.npos;
}

// base 는 뒤붙이 없는 이름 → 40글자 또는 "". §6.2 의 1‥5 차례.
std::string base(const std::string& gitdir, const std::string& name) {
    if (is_hex40(name) && !find_object(gitdir, name).empty())
        return name;
    if (name == "HEAD" || name == "ORIG_HEAD" || name == "MERGE_HEAD")
        return resolve_ref(gitdir, name);
    if (name.starts_with("refs/"))
        if (auto oid = resolve_ref(gitdir, name); !oid.empty())
            return oid;
    for (auto cand :
         {"refs/tags/" + name, "refs/heads/" + name,
          "refs/remotes/" + name, "refs/remotes/" + name + "/HEAD"})
        if (auto oid = resolve_ref(gitdir, cand); !oid.empty())
            return oid;
    try {
        return find_object(gitdir, name);
    } catch (const GitError&) {
        return "";  // 모호한 앞부분은 풀지 못한 것
    }
}
}  // namespace

// packed_refs 는 packed-refs → {이름: 40글자}. '#' 머리와 '^' 줄은
// 건너뛴다.
std::map<std::string, std::string> packed_refs(
    const std::string& gitdir) {
    std::map<std::string, std::string> out;
    std::istringstream in(
        try_read(gitdir + "/packed-refs").value_or(""));
    for (std::string line; std::getline(in, line);) {
        if (line.empty() || line[0] == '#' || line[0] == '^') continue;
        auto sp = line.find(' ');
        out[line.substr(sp + 1)] = line.substr(0, sp);
    }
    return out;
}

// read_ref 는 참조 하나. 없으면 nullopt. 느슨한 파일이 먼저다.
std::optional<Ref> read_ref(const std::string& gitdir,
                            const std::string& name) {
    if (auto text = try_read(gitdir + "/" + name)) {
        auto t = trim(*text);
        if (t.starts_with("ref: ")) return Ref{true, t.substr(5)};
        return Ref{false, t};
    }
    auto packed = packed_refs(gitdir);
    if (auto it = packed.find(name); it != packed.end())
        return Ref{false, it->second};
    return std::nullopt;
}

// resolve_ref 는 심볼릭 참조를 따라가 40글자. 없거나 태어나지 않았으면
// "".
std::string resolve_ref(const std::string& gitdir, std::string name) {
    for (int i = 0; i < 5; ++i) {
        auto r = read_ref(gitdir, name);
        if (!r) return "";
        if (!r->sym) return r->val;
        name = r->val;
    }
    throw GitError("fatal: mygit: symbolic ref loop at " + name);
}

// read_head 는 (HEAD 가 가리키는 브랜치 참조 이름 또는 "", 커밋 또는
// "").
std::pair<std::string, std::string> read_head(
    const std::string& gitdir) {
    auto r = read_ref(gitdir, "HEAD");
    if (!r) throw GitError("fatal: mygit: HEAD is missing");
    if (!r->sym) return {"", r->val};
    return {r->val, resolve_ref(gitdir, r->val)};
}

// list_refs 는 prefix 아래 참조들, 이름의 바이트 차례.
std::vector<NamedRef> list_refs(const std::string& gitdir,
                                const std::string& prefix) {
    std::map<std::string, std::string> found;
    for (auto& [n, o] : packed_refs(gitdir))
        if (n.starts_with(prefix)) found[n] = o;
    std::error_code ec;
    for (auto& e :
         fs::recursive_directory_iterator(gitdir + "/" + prefix, ec)) {
        auto p = e.path().string();
        if (!e.is_regular_file() || p.ends_with(".lock")) continue;
        auto name = fs::relative(e.path(), gitdir).generic_string();
        if (auto oid = resolve_ref(gitdir, name); !oid.empty())
            found[name] = oid;
    }
    std::vector<NamedRef> out;
    for (auto& [n, o] : found) out.push_back({n, o});
    return out;
}

// append_reflog 는 reflog 한 줄(SPEC.md §6.3) — "옛 새
// 신원<TAB>메시지".
void append_reflog(const std::string& gitdir, const std::string& name,
                   const std::string& old, const std::string& now,
                   const std::string& ident, const std::string& msg) {
    auto path = gitdir + "/logs/" + name;
    fs::create_directories(fs::path(path).parent_path());
    std::ofstream(path, std::ios::app | std::ios::binary)
        << (old.empty() ? ZERO : old) << ' '
        << (now.empty() ? ZERO : now) << ' ' << ident << '\t' << msg
        << '\n';
}

// read_reflog 는 오래된 것부터. 없으면 빈 목록.
std::vector<ReflogEntry> read_reflog(const std::string& gitdir,
                                     const std::string& name) {
    std::vector<ReflogEntry> out;
    std::istringstream in(
        try_read(gitdir + "/logs/" + name).value_or(""));
    for (std::string line; std::getline(in, line);) {
        if (line.empty()) continue;
        auto tab = line.find('\t');
        auto head = line.substr(0, tab);
        auto s1 = head.find(' '), s2 = head.find(' ', s1 + 1);
        out.push_back({head.substr(0, s1),
                       head.substr(s1 + 1, s2 - s1 - 1),
                       head.substr(s2 + 1), line.substr(tab + 1)});
    }
    return out;
}

// update_ref 는 참조 하나를 바꾸고 reflog 를 남긴다. now 가 "" 이면
// 지운다. HEAD 가 이 브랜치를 가리키고 있으면 HEAD 의 reflog 에도 같은
// 줄을 남긴다 — 커밋 하나가 두 로그에 모두 보이는 까닭.
void update_ref(const std::string& gitdir, const std::string& name,
                const std::string& now, const std::string& old,
                const std::string& msg, const std::string& ident) {
    auto path = gitdir + "/" + name;
    if (now.empty()) {
        if (!fs::exists(path))
            throw GitError("fatal: mygit: cannot delete packed ref " +
                           name);
        fs::remove(path);
        fs::remove(gitdir + "/logs/" + name);
        return;
    }
    write_locked(path, now + "\n");
    append_reflog(gitdir, name, old, now, ident, msg);
    auto head = read_ref(gitdir, "HEAD");
    if (name != "HEAD" && head && head->sym && head->val == name)
        append_reflog(gitdir, "HEAD", old, now, ident, msg);
}

// set_head 는 HEAD 를 브랜치(refs/heads/…)나 커밋(분리)으로. reflog 는
// 부르는 쪽이 적는다 — 메시지가 명령마다 다르다(§6.3 의 표).
void set_head(const std::string& gitdir, const std::string& target) {
    write_locked(
        gitdir + "/HEAD",
        (target.starts_with("refs/") ? "ref: " : "") + target + "\n");
}

// peel 은 태그를 벗겨 want('commit'·'tree')를 얻는다. 못 얻으면 "".
std::string peel(const std::string& gitdir, std::string oid,
                 const std::string& want) {
    for (int i = 0; i < 10; ++i) {
        auto o = read_object(gitdir, oid);
        auto first = o.body.substr(0, o.body.find('\n'));
        if (o.type == want) return oid;
        if (o.type == "tag")
            oid = first.substr(7);
        else if (o.type == "commit" && want == "tree")
            oid = first.substr(5);
        else
            return "";
    }
    return "";
}

// rev_parse 는 <rev> → 40글자 또는 "". ~n · ^n · ^0 · ^{tree} ·
// ^{commit}. 뒤붙이는 왼쪽부터 차례로 적용한다.
// O(뒤붙이의 길이 × 객체 읽기).
std::string rev_parse(const std::string& gitdir,
                      const std::string& spec) {
    size_t i = std::min(spec.find_first_of("~^"), spec.size());
    if (i == 0) return "";
    auto oid = base(gitdir, spec.substr(0, i));
    while (!oid.empty() && i < spec.size()) {
        char op = spec[i++];
        if (op == '^' && i < spec.size() && spec[i] == '{') {
            auto end = spec.find('}', i);
            if (end == spec.npos) return "";
            auto want = spec.substr(i + 1, end - i - 1);
            i = end + 1;
            oid = peel(gitdir, oid, want.empty() ? "commit" : want);
            continue;
        }
        size_t j = i;
        while (j < spec.size() && std::isdigit(uint8_t(spec[j]))) ++j;
        size_t n = j > i ? std::stoul(spec.substr(i, j - i)) : 1;
        i = j;
        oid = peel(gitdir, oid, "commit");
        if (oid.empty()) return "";
        if (op == '~') {
            for (size_t k = 0; k < n && !oid.empty(); ++k) {
                auto ps = parents_of(gitdir, oid);
                oid = ps.empty() ? "" : ps[0];
            }
        } else if (n) {
            auto ps = parents_of(gitdir, oid);
            oid = n <= ps.size() ? ps[n - 1] : "";
        }
    }
    return oid;
}

// valid_branch_name 은 SPEC.md §9.2 의 브랜치 이름 규칙
// (check-ref-format 의 일부).
bool valid_branch_name(const std::string& name) {
    if (name.empty() || name == "@" || name.find("..") != name.npos ||
        name.find("@{") != name.npos || name.find("//") != name.npos)
        return false;
    for (unsigned char c : name)
        if (c < 32 || c == 127 ||
            std::string(" ~^:?*[\\").find(char(c)) != std::string::npos)
            return false;
    return std::string("-./").find(name[0]) == std::string::npos &&
           !name.ends_with("/") && !name.ends_with(".") &&
           !name.ends_with(".lock");
}
}  // namespace mygit
