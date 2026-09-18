// merge (SPEC.md §12) — 공통 조상 B 에서 갈라진 O(우리)와 T(그들).
//
// 파일 하나의 합치기는 git 의 xdl_merge(ZEALOUS 수준)를 따른다:
//  1. B→O, B→T 의 바뀐 곳을 B 좌표로 짝지어 훑는다. 엄격히 앞선
//     쪽은 그대로 받고, 겹치거나 맞닿으면 충돌 후보다(같은 수정이면
//     한 번만).
//  2. 충돌마다 O 쪽과 T 쪽을 다시 diff 해 같은 줄을 표지 밖으로 뺀다.
//  3. 사이가 바뀌지 않은 줄 3개 이하인 이웃 충돌은 하나로 붙인다.
// 진짜 git merge 로 경계를 확인한 규칙들이다(golden/scen/merge-*.scn).
#include <set>

#include "mygit.hpp"

namespace mygit {
namespace {
const size_t join = 3;  // 이만큼 가까운 충돌은 하나로 붙인다

std::vector<Change> changes_of(const Lines& a, const Lines& b) {
    auto [ra, rb] = edit_flags(a, b);
    return build_changes(ra, rb);
}

Lines slice(const Lines& v, size_t a, size_t b) {
    return Lines(v.begin() + a, v.begin() + b);
}

// side_range 는 B 의 [start, end) 에 맞는 한쪽 파일의 범위. start
// 앞에서 시작한 바뀐 곳들의 길이 차를 더하면 시작 자리가, end 이하에서
// 시작한 것까지 더하면 끝 자리가 나온다.
std::pair<size_t, size_t> side_range(const std::vector<Change>& cs,
                                     size_t start, size_t end) {
    long s = long(start), e = long(end);
    for (auto& c : cs) {
        if (c.a < start) s += long(c.nb) - long(c.na);
        if (c.a <= end) e += long(c.nb) - long(c.na);
    }
    return {size_t(s), size_t(e)};
}

// Piece 는 결과의 한 조각. 's' 는 B 그대로(다듬기의 같은 줄 포함),
// 'c' 는 한쪽에서 받은 변경, 'x' 는 충돌(o·t 가 양쪽). 붙이기는 's'
// 만 사이에 둔 충돌끼리 한다 — 'c' 는 이웃을 끊는다.
struct Piece {
    char kind;
    Lines o, t;
};

// refine 은 2 단계 — 충돌 하나를 O·T 의 diff 로 쪼갠다. 같은 줄은 표지
// 밖으로 나온다. O == T 면 충돌이 아니다.
std::vector<Piece> refine(const Lines& o, const Lines& t) {
    if (o == t) return {{'s', o, {}}};
    std::vector<Piece> out;
    size_t p1 = 0;
    for (auto& c : changes_of(o, t)) {
        if (c.a > p1) out.push_back({'s', slice(o, p1, c.a), {}});
        out.push_back({'x', slice(o, c.a, c.a + c.na),
                       slice(t, c.b, c.b + c.nb)});
        p1 = c.a + c.na;
    }
    if (p1 < o.size()) out.push_back({'s', slice(o, p1, o.size()), {}});
    return out;
}

// pieces 는 1·2 단계 — 두 변경 목록을 B 좌표로 짝짓고 충돌을 다듬는다.
std::vector<Piece> pieces(const Lines& b, const Lines& o,
                          const Lines& t) {
    auto c1 = changes_of(b, o), c2 = changes_of(b, t);
    std::vector<Piece> out;
    size_t i = 0, j = 0, pos = 0;
    auto take = [&](size_t s, size_t e, Piece p) {
        if (s > pos) out.push_back({'s', slice(b, pos, s), {}});
        out.push_back(std::move(p));
        pos = e;
    };
    while (i < c1.size() || j < c2.size()) {
        if (j == c2.size() ||
            (i < c1.size() && c1[i].a + c1[i].na < c2[j].a)) {
            auto& x = c1[i++];
            take(x.a, x.a + x.na, {'c', slice(o, x.b, x.b + x.nb), {}});
            continue;
        }
        if (i == c1.size() || c2[j].a + c2[j].na < c1[i].a) {
            auto& y = c2[j++];
            take(y.a, y.a + y.na, {'c', slice(t, y.b, y.b + y.nb), {}});
            continue;
        }
        auto &x = c1[i], &y = c2[j];
        if (x.a == y.a && x.na == y.na &&
            slice(o, x.b, x.b + x.nb) == slice(t, y.b, y.b + y.nb)) {
            // 양쪽이 같은 수정 — 한 번만
            take(x.a, x.a + x.na, {'c', slice(o, x.b, x.b + x.nb), {}});
            ++i, ++j;
            continue;
        }
        size_t start = std::min(x.a, y.a),
               end = std::max(x.a + x.na, y.a + y.na);
        ++i, ++j;
        for (;;) {  // 맞닿는 것까지 넓힌다
            if (i < c1.size() && c1[i].a <= end) {
                end = std::max(end, c1[i].a + c1[i].na), ++i;
            } else if (j < c2.size() && c2[j].a <= end) {
                end = std::max(end, c2[j].a + c2[j].na), ++j;
            } else {
                break;
            }
        }
        auto [os, oe] = side_range(c1, start, end);
        auto [ts, te] = side_range(c2, start, end);
        if (start > pos) out.push_back({'s', slice(b, pos, start), {}});
        for (auto& p : refine(slice(o, os, oe), slice(t, ts, te)))
            out.push_back(p);
        pos = end;
    }
    if (pos < b.size())
        out.push_back({'s', slice(b, pos, b.size()), {}});
    return out;
}

std::string cat(const Lines& v) {
    std::string s;
    for (auto& l : v) s += l;
    return s;
}
}  // namespace

// merge3 은 세 판의 바이트 → (합친 바이트, 충돌 수). SPEC.md §12.3.
// O(줄 수 × 편집 거리) — diff 두 번과 충돌마다 diff 한 번.
std::pair<std::string, int> merge3(const std::string& base,
                                   const std::string& ours,
                                   const std::string& theirs,
                                   const std::string& label) {
    if (ours == theirs || base == theirs) return {ours, 0};
    if (base == ours) return {theirs, 0};
    // 3 단계 — 바뀌지 않은 줄 join 개 이하로 떨어진 충돌을 붙인다
    std::vector<Piece> joined;
    for (auto& p : pieces(split_lines(base), split_lines(ours),
                          split_lines(theirs))) {
        size_t n = joined.size();
        if (p.kind == 'x' && n >= 2 && joined[n - 1].kind == 's' &&
            joined[n - 2].kind == 'x' &&
            joined[n - 1].o.size() <= join) {
            auto mid = joined[n - 1].o;
            auto& prev = joined[n - 2];
            prev.o.insert(prev.o.end(), mid.begin(), mid.end());
            prev.o.insert(prev.o.end(), p.o.begin(), p.o.end());
            prev.t.insert(prev.t.end(), mid.begin(), mid.end());
            prev.t.insert(prev.t.end(), p.t.begin(), p.t.end());
            joined.pop_back();
        } else if (p.kind == 's' && n > 0 &&
                   joined[n - 1].kind == 's') {
            joined[n - 1].o.insert(joined[n - 1].o.end(), p.o.begin(),
                                   p.o.end());
        } else {
            joined.push_back(p);
        }
    }
    std::string out;
    int conflicts = 0;
    for (auto& p : joined) {
        if (p.kind != 'x') {
            out += cat(p.o);
            continue;
        }
        ++conflicts;
        out += "<<<<<<< HEAD\n" + cat(p.o) + "=======\n" + cat(p.t) +
               ">>>>>>> " + label + "\n";
    }
    return {out, conflicts};
}

// merge_trees 는 트리 단위 합치기(SPEC.md §12.2). 모드는 내용과 따로
// 같은 세 줄 규칙(O = T → O, B = T → O, B = O → T). 없음(nullopt)도
// 값이다 — 한쪽만 지웠으면 지움이 이긴다.
TreeMerge merge_trees(const std::string& gitdir, const TreeMap& base,
                      const TreeMap& ours, const TreeMap& theirs,
                      const std::string& label) {
    auto pick =
        [](const auto& b, const auto& o,
           const auto& t) -> std::optional<std::decay_t<decltype(o)>> {
        if (o == t || b == t) return o;
        if (b == o) return t;
        return std::nullopt;  // 못 고름
    };
    auto get = [](const TreeMap& m, const std::string& p) {
        auto it = m.find(p);
        return it == m.end() ? std::nullopt
                             : std::optional<Blob>(it->second);
    };
    std::set<std::string> all;
    for (auto* m : {&base, &ours, &theirs})
        for (auto& [p, _] : *m) all.insert(p);
    TreeMerge tm;
    for (auto& p : all) {
        auto bv = get(base, p), ov = get(ours, p), tv = get(theirs, p);
        if (auto whole = pick(bv, ov, tv)) {
            tm.result[p] =
                *whole ? MergeResult{false, false, **whole, "", {}}
                       : MergeResult{true, false, {}, "", {}};
            continue;
        }
        if (!ov || !tv)
            throw GitError(
                "fatal: mygit: unsupported merge case (modify/delete) "
                "in " +
                p);
        auto mode =
            pick(bv ? std::optional(bv->mode) : std::nullopt,
                 std::optional(ov->mode), std::optional(tv->mode));
        if (!mode)
            throw GitError(
                "fatal: mygit: unsupported merge case (mode) in " + p);
        tm.notes.push_back("Auto-merging " + p);
        auto body = [&](const std::optional<Blob>& v) {
            return v ? read_object(gitdir, v->oid).body : "";
        };
        auto [text, n] = merge3(body(bv), body(ov), body(tv), label);
        if (!n) {
            tm.result[p].blob = {**mode,
                                 write_object(gitdir, "blob", text)};
            continue;
        }
        auto& r = tm.result[p];
        r.conflict = true, r.text = text, r.blob = {**mode, ""};
        r.stages = {{2, *ov}, {3, *tv}};
        if (bv) r.stages[1] = *bv;
        tm.notes.push_back("CONFLICT (" +
                           std::string(bv ? "content" : "add/add") +
                           "): Merge conflict in " + p);
        tm.conflicts.push_back(p);
    }
    return tm;
}
}  // namespace mygit
