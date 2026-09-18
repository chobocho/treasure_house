// 역사 걷기와 merge-base (SPEC.md §10).
//
// git 의 기본 log 차례는 "커미터 날짜가 늦은 것부터" 인데, 날짜가 같을
// 때의 규칙까지 정해져 있다 — 날짜 차례로 정렬된 목록에 새 커밋을
// 끼울 때 같은 날짜들 가운데 맨 뒤에 끼운다(git 의 commit_list_
// insert_by_date). 이 덱의 저장소는 모든 커밋의 날짜가 같게 만들어지
// 므로, 이 한 줄이 차례의 전부를 정한다.
#include <algorithm>
#include <set>

#include "mygit.hpp"

namespace mygit {
namespace {
struct Info {
    std::vector<std::string> parents;
    long long when;
};

// info 는 (부모 목록, 커미터 날짜 초). 한 번 읽은 커밋은 기억한다 —
// 커밋은 바뀌지 않으니 지울 일이 없다.
const Info& info(const std::string& gitdir, const std::string& oid) {
    static std::map<std::string, Info> cache;
    auto key = gitdir + "\n" + oid;
    auto it = cache.find(key);
    if (it != cache.end()) return it->second;
    auto c = parse_commit(read_object(gitdir, oid).body);
    return cache[key] = {c.parents, parse_ident(c.committer).secs};
}

// ancestors 는 oid 와 그 조상 전부의 집합. O(커밋 수).
std::set<std::string> ancestors(const std::string& gitdir,
                                const std::string& oid) {
    std::set<std::string> seen;
    std::vector<std::string> stack{oid};
    while (!stack.empty()) {
        auto c = stack.back();
        stack.pop_back();
        if (!seen.insert(c).second) continue;
        for (auto& p : info(gitdir, c).parents) stack.push_back(p);
    }
    return seen;
}
}  // namespace

// walk_log 는 시작 커밋들에서 닿는 커밋 전부, git log 의 기본 차례로.
// 큐는 날짜 내림차순 목록이다. 끼울 자리는 "날짜가 같거나 늦은 것들
// 바로 뒤" — 그래서 같은 날짜라면 먼저 들어온 것이 먼저 나간다.
// O(커밋 수 × log(큐 길이)) 비교, 끼우기는 목록이라 O(큐 길이).
std::vector<std::string> walk_log(
    const std::string& gitdir, const std::vector<std::string>& starts) {
    std::vector<std::pair<long long, std::string>> queue;
    std::set<std::string> seen;
    std::vector<std::string> out;
    auto push = [&](const std::string& oid) {
        if (!seen.insert(oid).second) return;
        long long when = info(gitdir, oid).when;
        auto at = std::find_if(queue.begin(), queue.end(),
                               [&](auto& q) { return q.first < when; });
        queue.insert(at, {when, oid});
    };
    for (auto& s : starts) push(s);
    while (!queue.empty()) {
        auto oid = queue.front().second;
        queue.erase(queue.begin());
        out.push_back(oid);
        for (auto& p : info(gitdir, oid).parents) push(p);
    }
    return out;
}

// is_ancestor 는 a 가 b 이거나 b 의 조상인가.
bool is_ancestor(const std::string& gitdir, const std::string& a,
                 const std::string& b) {
    return ancestors(gitdir, b).count(a) > 0;
}

// merge_bases 는 가장 좋은 공통 조상들(SPEC.md §10.2), 커미터 날짜
// 내림차순. 공통 조상 가운데 다른 공통 조상의 조상이 아닌 것만
// 남긴다. 작은 저장소를 위한 곧은 방법이다 — git 은 날짜로 칠하며
// 내려가는 더 빠른 길(paint_down_to_common)을 쓴다. O(커밋 수²) 최악.
std::vector<std::string> merge_bases(const std::string& gitdir,
                                     const std::string& a,
                                     const std::string& b) {
    auto aa = ancestors(gitdir, a), bb = ancestors(gitdir, b);
    std::set<std::string> below;
    std::vector<std::string> common, best;
    for (auto& c : aa) {
        if (!bb.count(c)) continue;
        common.push_back(c);
        for (auto& p : info(gitdir, c).parents)
            for (auto& x : ancestors(gitdir, p)) below.insert(x);
    }
    for (auto& c : common)
        if (!below.count(c)) best.push_back(c);
    // 날짜가 같으면 이름 차례 — 집합의 차례가 결과에 새지 않게
    std::stable_sort(best.begin(), best.end(), [&](auto& x, auto& y) {
        return info(gitdir, x).when > info(gitdir, y).when;
    });
    return best;
}
}  // namespace mygit
