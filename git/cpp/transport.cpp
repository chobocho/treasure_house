// 전송 (SPEC.md §14) — 저장소끼리 객체와 참조를 나누는 법.
//
// pkt-line 은 "길이 네 자리 16진 + 데이터" 다. 길이가 자기 4바이트를
// 품는 까닭은 0000(flush)·0001(delim) 같은 특별한 값을 데이터와
// 헷갈리지 않게 하려는 것이다. 여기에는 두 가지가 있다: 협상 없이
// 객체 파일을 그대로 복사하는 "멍청한" 로컬 clone, 그리고 진짜 git
// upload-pack 을 자식으로 띄워 프로토콜 v2 로 말하는 fetch-pack(서버는
// 짜지 않는다 — PLAN.md §9 결정 8).
#include <signal.h>
#include <sys/wait.h>
#include <unistd.h>

#include <algorithm>
#include <cstdio>
#include <filesystem>
#include <fstream>

#include "mygit.hpp"

namespace fs = std::filesystem;

namespace mygit {
namespace {
const std::string flush = "0000", delim = "0001";

// Wire 는 자식 upload-pack 과의 pkt-line 대화. 기록은 §14.3 의 꼴.
// 소멸자가 파이프를 닫고 자식을 거둔다 — 도중에 오류가 나도 좀비가
// 남지 않는다.
struct Wire {
    pid_t pid = -1;
    int to = -1, from = -1;
    std::vector<std::string> log;

    Wire(const std::string& src, const Env& env) {
        int in[2], out[2];
        if (pipe(in) || pipe(out))
            throw GitError("fatal: mygit: cannot create pipe");
        std::vector<std::string> vars;
        for (auto& [k, v] : env) vars.push_back(k + "=" + v);
        vars.push_back("GIT_PROTOCOL=version=2");
        pid = fork();
        if (pid == 0) {
            dup2(in[0], 0), dup2(out[1], 1);
            for (int fd : {in[0], in[1], out[0], out[1]}) close(fd);
            std::vector<char*> envp, argv;
            for (auto& v : vars) envp.push_back(v.data());
            envp.push_back(nullptr);
            std::string a0 = "git", a1 = "upload-pack", a2 = src;
            argv = {a0.data(), a1.data(), a2.data(), nullptr};
            execvpe("git", argv.data(), envp.data());
            _exit(127);
        }
        close(in[0]), close(out[1]);
        to = in[1], from = out[0];
    }
    ~Wire() {
        if (to >= 0) close(to);
        if (from >= 0) close(from);
        if (pid > 0 && waitpid(pid, nullptr, WNOHANG) == 0) {
            kill(pid, SIGTERM);
            waitpid(pid, nullptr, 0);
        }
    }

    void send(const std::vector<std::string>& items) {
        std::string buf;
        for (auto& it : items) {
            bool special = it == flush || it == delim;
            log.push_back("> " + (special ? it : render(it)));
            buf += special ? it : pkt_line(it);
        }
        for (size_t k = 0; k < buf.size();) {
            auto n = write(to, buf.data() + k, buf.size() - k);
            if (n <= 0) throw GitError("fatal: mygit: remote hung up");
            k += size_t(n);
        }
    }

    std::string exact(size_t n) {
        std::string buf(n, '\0');
        for (size_t k = 0; k < n;) {
            auto got = read(from, buf.data() + k, n - k);
            if (got <= 0)
                throw GitError(
                    "fatal: mygit: remote hung up unexpectedly");
            k += size_t(got);
        }
        return buf;
    }

    // read 는 flush 까지의 패킷들. packfile 절 뒤의 사이드밴드 1 은
    // pack 으로 모은다(2 는 진행 안내, 3 은 원격의 오류).
    std::vector<std::string> read_until_flush(
        std::string* pack = nullptr) {
        std::vector<std::string> lines;
        bool side = false;
        for (;;) {
            size_t n = std::stoul(exact(4), nullptr, 16);
            char head[8];
            std::snprintf(head, sizeof head, "%04zx", n);
            if (n < 4) {
                log.push_back(std::string("< ") + head);
                if (n == 0) return lines;
                continue;
            }
            auto data = exact(n - 4);
            if (side && data[0] == 1) {
                pack->append(data, 1);
                log.push_back(std::string("< ") + head + " [pack " +
                              std::to_string(n - 5) + " bytes]");
                continue;
            }
            if (side && data[0] == 3)
                throw GitError("fatal: mygit: remote error: " +
                               data.substr(1));
            log.push_back("< " + render(data));
            if (data == "packfile\n") side = pack != nullptr;
            lines.push_back(data);
        }
    }
};
}  // namespace

// pkt_line 은 데이터 → pkt-line 한 개.
std::string pkt_line(std::string_view data) {
    if (data.size() > 65516)
        throw GitError("fatal: mygit: pkt-line too long");
    char head[8];
    std::snprintf(head, sizeof head, "%04zx", data.size() + 4);
    return head + std::string(data);
}

// render 는 대화 기록의 꼴(SPEC.md §14.3) — 길이 + 파이썬 repr 식
// 이스케이프. 기준 기록을 파이썬이 썼으므로 따옴표 고르기까지 따른다:
// 작은따옴표만 있고 큰따옴표가 없으면 repr 은 큰따옴표로 감싸고 ' 를
// 그대로 둔다.
std::string render(std::string_view data) {
    char quote =
        data.find('\'') != data.npos && data.find('"') == data.npos
            ? '"'
            : '\'';
    char head[8];
    std::snprintf(head, sizeof head, "%04zx", data.size() + 4);
    std::string out = head;
    for (unsigned char c : data) {
        if (c == '\\' || c == quote)
            out += '\\', out += char(c);
        else if (c == '\t')
            out += "\\t";
        else if (c == '\n')
            out += "\\n";
        else if (c == '\r')
            out += "\\r";
        else if (c < 32 || c >= 127) {
            char buf[8];
            std::snprintf(buf, sizeof buf, "\\x%02x", c);
            out += buf;
        } else {
            out += char(c);
        }
    }
    return out;
}

// clone_local 은 src 의 객체 파일을 그대로 복사하고 참조를 세운다.
// → 브랜치 이름. 협상이 없다 — 받는 쪽이 이미 가진 것도 다시
// 복사한다. 그래도 객체의 이름이 곧 내용이므로 옮긴 파일은 어느
// 저장소에서나 같은 객체다(SPEC.md §14.2).
std::string clone_local(const std::string& src, const std::string& dst,
                        const std::string& ident) {
    auto sg = fs::is_directory(src + "/.git") ? src + "/.git" : src;
    auto g = dst + "/.git";
    for (auto& e : fs::recursive_directory_iterator(sg + "/objects")) {
        if (!e.is_regular_file()) continue;
        auto ext = e.path().extension();
        if (e.path().parent_path().filename() == "pack" &&
            ext != ".pack" && ext != ".idx")
            continue;
        auto to = g / fs::relative(e.path(), sg);
        fs::create_directories(to.parent_path());
        fs::copy_file(e.path(), to,
                      fs::copy_options::overwrite_existing);
    }
    auto head = read_ref(sg, "HEAD");
    auto branch = head && head->sym ? head->val.substr(11) : "";
    for (auto& r : list_refs(sg)) {
        std::string local;
        if (r.name.starts_with("refs/heads/"))
            local = "refs/remotes/origin/" + r.name.substr(11);
        else if (r.name.starts_with("refs/tags/"))
            local = r.name;
        else
            continue;
        fs::create_directories(fs::path(g + "/" + local).parent_path());
        std::ofstream(g + "/" + local, std::ios::binary)
            << r.oid + "\n";
    }
    if (branch.empty())
        throw GitError("fatal: mygit: source HEAD is detached");
    fs::create_directories(g + "/refs/remotes/origin");
    std::ofstream(g + "/refs/remotes/origin/HEAD", std::ios::binary)
        << "ref: refs/remotes/origin/" + branch + "\n";
    auto oid = resolve_ref(sg, "refs/heads/" + branch);
    auto abs = fs::absolute(src).lexically_normal().string();
    if (abs.size() > 1 && abs.back() == '/') abs.pop_back();
    set_head(g, "refs/heads/" + branch);
    update_ref(g, "refs/heads/" + branch, oid, "", "clone: from " + abs,
               ident);
    std::ofstream(g + "/config", std::ios::binary | std::ios::app)
        << "[remote \"origin\"]\n\turl = " + abs +
               "\n\tfetch = +refs/heads/*:refs/remotes/origin/*\n"
               "[branch \"" +
               branch +
               "\"]\n\tremote = origin\n"
               "\tmerge = refs/heads/" +
               branch + "\n";
    checkout_tree(dst, g, "", peel(g, oid, "tree"));
    return branch;
}

// fetch_pack 은 want_refs 를 받아 팩을 저장한다. → (이름, 참조) 들.
// 참조는 고치지 않는다 — 그것은 fetch 의 일이다(SPEC.md §14.3 의 5).
std::vector<NamedRef> fetch_pack(
    const std::string& gitdir, const std::string& src,
    const std::vector<std::string>& want_refs, const Env& env,
    const std::string& log_path) {
    Wire w(src, env);
    auto caps = w.read_until_flush();
    bool fetch = std::any_of(caps.begin(), caps.end(), [](auto& c) {
        return c.starts_with("fetch");
    });
    if (caps.empty() || caps[0] != "version 2\n" || !fetch)
        throw GitError(
            "fatal: mygit: server does not speak protocol v2");
    std::vector<std::string> req = {"command=ls-refs\n",
                                    "object-format=sha1\n", delim,
                                    "peel\n", "symrefs\n"};
    for (auto& r : want_refs) req.push_back("ref-prefix " + r + "\n");
    req.push_back(flush);
    w.send(req);
    std::map<std::string, std::string> adv;
    for (auto& line : w.read_until_flush()) {
        auto sp = line.find(' ');
        auto name = line.substr(
            sp + 1, line.find_first_of(" \n", sp + 1) - sp - 1);
        adv[name] = line.substr(0, sp);
    }
    std::vector<std::string> wants, haves;
    for (auto& r : want_refs) {
        if (!adv.count(r))
            throw GitError("fatal: mygit: no such remote ref " + r);
        if (std::find(wants.begin(), wants.end(), adv[r]) ==
            wants.end())
            wants.push_back(adv[r]);
    }
    for (auto& r : list_refs(gitdir))
        if (std::find(haves.begin(), haves.end(), r.oid) == haves.end())
            haves.push_back(r.oid);
    req = {"command=fetch\n", "object-format=sha1\n", delim,
           "ofs-delta\n", "no-progress\n"};
    for (auto& o : wants) req.push_back("want " + o + "\n");
    for (auto& o : haves) req.push_back("have " + o + "\n");
    req.push_back("done\n");
    req.push_back(flush);
    w.send(req);
    std::string data;
    w.read_until_flush(&data);
    if (!log_path.empty()) {
        std::ofstream f(log_path, std::ios::binary);
        for (auto& l : w.log) f << l << '\n';
    }
    auto ents = read_pack(
        data, [&](auto& o) { return read_object(gitdir, o); });
    auto sum = data.substr(data.size() - 20);
    auto stem = gitdir + "/objects/pack/pack-" + to_hex(sum);
    fs::create_directories(gitdir + "/objects/pack");
    std::ofstream(stem + ".pack", std::ios::binary) << data;
    std::ofstream(stem + ".idx", std::ios::binary)
        << write_idx(ents, sum);
    std::vector<NamedRef> got;
    for (auto& r : want_refs) got.push_back({r, adv[r]});
    return got;
}
}  // namespace mygit
