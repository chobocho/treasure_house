// tree (SPEC.md §4.3) — 디렉터리 하나를 객체 하나로.
//
// 항목 = "<모드> <이름>\0<객체 이름 20바이트>". 이름과 권한은 blob 이
// 아니라 트리가 갖는다 — 같은 내용의 파일 둘은 blob 하나를 나눠 쓴다.
//
// 정렬 규칙이 전부다. 항목은 이름의 바이트로 정렬하되 하위 트리는
// 이름 뒤에 '/' 가 붙은 것처럼 비교한다. std::string 의 < 는 char 를
// 부호 없는 것처럼 견주므로(char_traits::lt) 곧 바이트 비교다.
#include <algorithm>

#include "mygit.hpp"

namespace mygit {
std::string tree_entry_key(const std::string& mode,
                           const std::string& name) {
    return mode == DIR ? name + "/" : name;
}

// parse_tree 는 트리 몸 → 항목들, 적힌 차례 그대로. O(몸의 길이).
std::vector<TreeEntry> parse_tree(std::string_view body) {
    std::vector<TreeEntry> out;
    for (size_t i = 0; i < body.size();) {
        auto sp = body.find(' ', i);
        auto nul = sp == body.npos ? sp : body.find('\0', sp + 1);
        if (nul == body.npos || nul + 21 > body.size())
            throw GitError("fatal: mygit: corrupt tree object");
        out.push_back({std::string(body.substr(i, sp - i)),
                       std::string(body.substr(sp + 1, nul - sp - 1)),
                       to_hex(body.substr(nul + 1, 20))});
        i = nul + 21;
    }
    return out;
}

// serialize_tree 는 항목들 → 트리 몸. 정렬은 여기서 한다. 모드는 앞에
// 0 을 붙이지 않는다 — '040000' 은 cat-file -p 가 찍는 꼴일 뿐이다.
std::string serialize_tree(std::vector<TreeEntry> ents) {
    std::sort(ents.begin(), ents.end(), [](auto& a, auto& b) {
        return tree_entry_key(a.mode, a.name) <
               tree_entry_key(b.mode, b.name);
    });
    std::string out;
    for (auto& e : ents)
        out += e.mode + " " + e.name + '\0' + from_hex(e.oid);
    return out;
}

// write_tree 는 (모드, blob 이름, 경로) 들 → 뿌리 트리 이름. 경로를
// '/' 로 나눠 디렉터리마다 트리를 짓고 아래에서 위로 쓴다.
// O(항목 수 × 깊이 + 정렬).
std::string write_tree(const std::string& gitdir,
                       const std::vector<PathEntry>& entries) {
    std::vector<TreeEntry> here;
    std::map<std::string, std::vector<PathEntry>> subdirs;
    for (auto& e : entries) {
        auto slash = e.path.find('/');
        if (slash == e.path.npos)
            here.push_back({e.mode, e.path, e.oid});
        else
            subdirs[e.path.substr(0, slash)].push_back(
                {e.mode, e.oid, e.path.substr(slash + 1)});
    }
    for (auto& [name, sub] : subdirs)
        here.push_back({DIR, name, write_tree(gitdir, sub)});
    return write_object(gitdir, "tree", serialize_tree(here));
}

// flatten_tree 는 트리를 재귀로 펼친다. 하위 트리는 항목으로 남기지
// 않고 그 안을 펼친다. 차례는 전체 경로의 바이트 차례와 같다.
std::vector<PathEntry> flatten_tree(const std::string& gitdir,
                                    const std::string& oid,
                                    const std::string& prefix) {
    auto o = read_object(gitdir, oid);
    if (o.type != "tree")
        throw GitError("fatal: mygit: " + oid + " is not a tree");
    std::vector<PathEntry> out;
    for (auto& e : parse_tree(o.body)) {
        if (e.mode != DIR) {
            out.push_back({e.mode, e.oid, prefix + e.name});
            continue;
        }
        auto sub = flatten_tree(gitdir, e.oid, prefix + e.name + "/");
        out.insert(out.end(), sub.begin(), sub.end());
    }
    return out;
}

// type_of_mode 는 cat-file -p 가 찍는 형식 — 모드에서 정해진다.
std::string type_of_mode(const std::string& mode) {
    return mode == DIR ? "tree" : mode == "160000" ? "commit" : "blob";
}
}  // namespace mygit
