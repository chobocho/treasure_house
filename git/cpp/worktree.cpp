// 작업 트리 (SPEC.md §8) — 경로 따옴표, 훑기, status.
//
// status 는 세 가지를 견준다: HEAD 트리, 인덱스, 디스크의 파일. 두 칸
// 글자(XY)가 곧 "어느 두 곳이 다른가" 다 — X 는 HEAD 와 인덱스, Y 는
// 인덱스와 작업 트리.
#include <sys/stat.h>

#include <algorithm>
#include <cstdio>
#include <filesystem>
#include <set>

#include "mygit.hpp"

namespace mygit {
// quote_path 는 경로 → git 이 사람에게 찍는 꼴(core.quotePath=true).
// 제어 문자·DEL·따옴표·역슬래시·0x80 이상 바이트가 하나라도 있으면
// 전체를 따옴표로 감싸고 C 식으로 쓴다(8진 세 자리). space 는 status
// 의 규칙 — 공백만 있어도 감싼다. O(경로 길이).
std::string quote_path(std::string_view path, bool space) {
    // \a \b \t \n \v \f \r 와 따옴표·역슬래시는 두 글자로 쓴다
    static const std::string from = "\a\b\t\n\v\f\r\"\\",
                             to = "abtnvfr\"\\";
    bool need = space && path.find(' ') != path.npos;
    std::string body;
    for (unsigned char c : path) {
        if (auto k = from.find(char(c)); k != from.npos) {
            body += '\\', body += to[k], need = true;
        } else if (c < 32 || c >= 127) {
            char buf[5];
            std::snprintf(buf, sizeof buf, "\\%03o", c);
            body += buf, need = true;
        } else {
            body += char(c);
        }
    }
    return need ? '"' + body + '"' : body;
}

// walk_worktree 는 작업 트리의 보통 파일 경로들, 전체 경로의 바이트
// 차례. 어느 깊이에서든 '.git' 은 건너뛰고, 심볼릭 링크와 장치 파일은
// 없는 것으로 본다(SPEC.md §8.1). O(파일 수 · log).
std::vector<std::string> walk_worktree(const std::string& root) {
    namespace fs = std::filesystem;
    std::vector<std::string> out;
    auto it = fs::recursive_directory_iterator(root);
    for (auto& e : it) {
        if (e.path().filename() == ".git") {
            if (e.is_directory()) it.disable_recursion_pending();
            continue;
        }
        if (e.is_symlink()) continue;
        if (e.is_regular_file())
            out.push_back(
                fs::relative(e.path(), root).generic_string());
    }
    std::sort(out.begin(), out.end());
    return out;
}

// file_state 는 디스크 파일의 (모드, blob 이름), 없으면 nullopt. 늘
// 해시한다 — stat 캐시를 믿지 않으니 racy git 이 없다(SPEC.md §7.2).
std::optional<Blob> file_state(const std::string& root,
                               const std::string& path) {
    auto p = root + "/" + path;
    struct stat st;
    if (lstat(p.c_str(), &st) != 0 || !S_ISREG(st.st_mode))
        return std::nullopt;
    auto data = try_read(p);
    if (!data) return std::nullopt;
    return Blob{st.st_mode & 0100 ? 0100755u : 0100644u,
                hash_object("blob", *data)};
}

// tree_map 은 트리 → {경로: Blob}. 트리가 없으면(첫 커밋 전) 빈 것.
TreeMap tree_map(const std::string& gitdir, const std::string& tree) {
    TreeMap out;
    if (tree.empty()) return out;
    for (auto& e : flatten_tree(gitdir, tree))
        out[e.path] = {uint32_t(std::stoul(e.mode, nullptr, 8)), e.oid};
    return out;
}

// head_tree 는 HEAD 커밋의 트리, 태어나지 않았으면 "".
std::string head_tree(const std::string& gitdir) {
    auto head = read_head(gitdir).second;
    return head.empty() ? "" : peel(gitdir, head, "tree");
}

namespace {
// untracked 는 추적하지 않는 파일들을 git 의 normal 모드로 접는다
// (§8.3). 파일마다 위쪽 디렉터리부터 보며, 그 아래에 인덱스 항목이
// 하나도 없는 첫 디렉터리가 있으면 "그 디렉터리/" 로 접는다.
// O(파일 × 깊이).
std::set<std::string> untracked(const std::vector<std::string>& files,
                                const std::set<std::string>& tracked) {
    std::set<std::string> dirs, out;
    for (auto& t : tracked)
        for (size_t i = t.find('/'); i != t.npos;
             i = t.find('/', i + 1))
            dirs.insert(t.substr(0, i));
    for (auto& f : files) {
        if (tracked.count(f)) continue;
        auto shown = f;
        for (size_t i = f.find('/'); i != f.npos;
             i = f.find('/', i + 1))
            if (!dirs.count(f.substr(0, i))) {
                shown = f.substr(0, i + 1);
                break;
            }
        out.insert(shown);
    }
    return out;
}
}  // namespace

// status 는 git status --porcelain 과 같은 줄들(SPEC.md §8.3).
// X = HEAD 트리 ↔ 인덱스, Y = 인덱스 ↔ 작업 트리. 추적 중인 것을
// 경로 차례로 먼저, 그다음 '?? ' 줄들. O(파일 수 × 해시).
std::vector<std::string> status(const std::string& root,
                                const std::string& gitdir) {
    // 충돌 경로의 두 글자 — 단계 1·2·3 이 있는가(비트 0·1·2) → XY
    static const std::map<int, std::string> unmerged = {
        {6, "AA"}, {7, "UU"}, {3, "UD"}, {5, "DU"},
        {2, "AU"}, {4, "UA"}, {1, "DD"}};
    auto base = tree_map(gitdir, head_tree(gitdir));
    TreeMap stage0;
    std::map<std::string, int> stages;
    std::set<std::string> all, tracked;
    for (auto& [p, _] : base) all.insert(p);
    for (auto& e : read_index(gitdir)) {
        all.insert(e.path), tracked.insert(e.path);
        if (e.stage)
            stages[e.path] |= 1 << (e.stage - 1);
        else
            stage0[e.path] = {e.mode, e.oid};
    }
    std::vector<std::string> rows;
    for (auto& p : all) {
        std::string xy;
        if (stages.count(p)) {
            xy = unmerged.at(stages[p]);
        } else {
            auto cur = stage0.find(p);
            auto old = base.find(p);
            char x = cur == stage0.end()          ? 'D'
                     : old == base.end()          ? 'A'
                     : cur->second == old->second ? ' '
                                                  : 'M';
            char y = ' ';
            if (cur != stage0.end()) {
                auto now = file_state(root, p);
                y = !now ? 'D' : *now != cur->second ? 'M' : ' ';
            }
            xy = {x, y};
        }
        if (xy != "  ") rows.push_back(xy + " " + quote_path(p, true));
    }
    for (auto& p : untracked(walk_worktree(root), tracked))
        rows.push_back("?? " + quote_path(p, true));
    return rows;
}
}  // namespace mygit
