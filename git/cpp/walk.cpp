// 역사 걷기와 merge-base (SPEC.md §10).
//
// git 의 기본 log 차례는 "커미터 날짜가 늦은 것부터" 인데, 날짜가 같을
// 때의 규칙까지 정해져 있다 — 날짜 차례로 정렬된 목록에 새 커밋을
// 끼울 때 같은 날짜들 가운데 맨 뒤에 끼운다(git 의 commit_list_
// insert_by_date). 이 덱의 저장소는 모든 커밋의 날짜가 같게 만들어지
// 므로, 이 한 줄이 차례의 전부를 정한다.
#include <algorithm>
#include <queue>
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

// paint 는 git 의 paint_down_to_common(commit-reach.c)이 공통 조상
// 후보를 찾는 차례 — SPEC.md §10.2 의 1~4. 큐는 날짜 내림차순, 같으면
// 넣은 차례(seq)가 빠른 것이 먼저. 표시는 P1(a 에서 닿음)·P2(b 에서
// 닿음)·STALE(이미 찾은 후보의 조상). "넣을 때 STALE 이 아니었던"
// 커밋이 큐에 남아 있는 동안 돈다(git 의 max_nonstale).
// O(커밋 수 × log 커밋 수) 시간, O(커밋 수) 공간.
static std::vector<std::string> paint(const std::string& gitdir,
                                      const std::string& a,
                                      const std::string& b) {
    enum { P1 = 1, P2 = 2, STALE = 4 };
    struct Slot {
        int64_t when;
        uint64_t seq;
        std::string oid;
        // priority_queue 는 가장 "큰" 것을 먼저 내준다
        bool operator<(const Slot& o) const {
            if (when != o.when) return when < o.when;
            return seq > o.seq;
        }
    };
    std::map<std::string, int> flags;
    std::map<std::string, bool> queued;  // 넣을 때 STALE 이 아니었나
    std::priority_queue<Slot> q;
    uint64_t seq = 0;
    int live = 0;
    auto put = [&](const std::string& c) {
        if (queued.count(c)) return;  // 이미 큐에 있으면 자리는 그대로
        bool fresh = !(flags[c] & STALE);
        queued[c] = fresh;
        if (fresh) ++live;
        q.push({info(gitdir, c).when, seq++, c});
    };
    flags[a] = P1;
    put(a);
    flags[b] |= P2;
    put(b);
    std::vector<std::string> found;
    while (live > 0) {
        std::string c = q.top().oid;
        q.pop();
        if (queued[c]) --live;
        queued.erase(c);
        int f = flags[c] & (P1 | P2 | STALE);
        if (f == (P1 | P2)) {
            if (std::find(found.begin(), found.end(), c) == found.end())
                found.push_back(c);
            f |= STALE;
        }
        for (auto& p : info(gitdir, c).parents) {
            if ((flags[p] & f) == f) continue;
            flags[p] |= f;
            put(p);
        }
    }
    std::vector<std::string> out;
    for (auto& c : found)
        if (!(flags[c] & STALE)) out.push_back(c);
    return out;
}

// merge_bases 는 가장 좋은 공통 조상들(SPEC.md §10.2) — git 과 같은
// 차례로. paint 가 찾은 후보에서 다른 후보의 조상인 것을 차례를
// 지키며 빼고(git 의 remove_redundant), 커미터 날짜 내림차순으로 안정
// 정렬한다. 날짜가 같으면 찾은 차례가 남아 인자 순서에 따라 답의
// 차례가 바뀐다 — git 도 그렇다. O(커밋 수 × 후보 수).
std::vector<std::string> merge_bases(const std::string& gitdir,
                                     const std::string& a,
                                     const std::string& b) {
    auto cands = paint(gitdir, a, b);
    std::vector<std::string> best;
    for (auto& c : cands) {
        bool redundant = false;
        for (auto& o : cands)
            if (o != c && is_ancestor(gitdir, c, o)) {
                redundant = true;
                break;
            }
        if (!redundant) best.push_back(c);
    }
    std::stable_sort(best.begin(), best.end(), [&](auto& x, auto& y) {
        return info(gitdir, x).when > info(gitdir, y).when;
    });
    return best;
}
}  // namespace mygit
