// diff (SPEC.md §11) — 두 줄 목록 사이의 가장 짧은 편집 스크립트.
//
// 세 단계다. (1) 앞뒤의 같은 줄을 떼어 둔다. (2) 남은 가운데서 Myers
// 의 탐욕 탐색으로 가장 짧은 스크립트를 찾는다. (3) 바뀐 줄 묶음을
// git 처럼 위아래로 밀어 자리를 정한다 — 같은 줄이 되풀이되는 곳에서는
// 어디를 바뀐 줄로 칠지가 여럿이라, 이 단계가 없으면 git 과 덩어리
// 자리가 달라진다. 줄은 줄바꿈까지 품는다.
#include <sys/stat.h>

#include <algorithm>
#include <cctype>

#include "mygit.hpp"

namespace mygit {
namespace {
const size_t context = 3, binary_probe = 8000;

// ── 2 단계: Myers 앞방향 탐욕 탐색 (SPEC.md §11.2) ─────────────────

// backtrack 은 (N, M) 에서 거꾸로 같은 판정을 되밟아 편집을 표시한다.
// trace[d] 는 d 단계를 시작할 때의 v 에서 [-d, d] 조각이다.
std::pair<Flags, Flags> backtrack(
    const std::vector<std::vector<long>>& trace, long n, long m,
    long dfin) {
    Flags ra(n), rb(m);
    long x = n, y = m;
    for (long d = dfin; d > 0; --d) {
        auto v = [&](long k) { return trace[d][k + d]; };
        long k = x - y;
        bool down = k == -d || (k != d && v(k - 1) < v(k + 1));
        long pk = down ? k + 1 : k - 1, px = v(pk), py = px - pk;
        if (down)
            rb[py] = true;
        else
            ra[px] = true;
        x = px, y = py;
    }
    return {ra, rb};
}

// forward 는 가운데 a·b 의 (ra, rb). 대각선 k 마다 가장 멀리 간 x 를
// v[k] 에 둔다. O((N+M)·D) 시간, O(D²) 공간.
std::pair<Flags, Flags> forward(const Lines& a, const Lines& b) {
    long n = long(a.size()), m = long(b.size()), off = n + m + 1;
    std::vector<long> v(2 * off + 1);
    std::vector<std::vector<long>> trace;
    for (long d = 0; d <= n + m; ++d) {
        trace.emplace_back(v.begin() + off - d,
                           v.begin() + off + d + 1);
        for (long k = -d; k <= d; k += 2) {
            long x =
                k == -d || (k != d && v[off + k - 1] < v[off + k + 1])
                    ? v[off + k + 1]       // 아래로: b 의 줄을 끼움
                    : v[off + k - 1] + 1;  // 오른쪽: a 의 줄을 지움
            long y = x - k;
            while (x < n && y < m && a[x] == b[y]) ++x, ++y;
            v[off + k] = x;
            if (x >= n && y >= m) return backtrack(trace, n, m, d);
        }
    }
    throw std::logic_error("Myers 탐색이 끝나지 않았다");
}

// ── 3 단계: 밀어 붙이기 (git 의 xdl_change_compact, 휴리스틱 없이) ──

// Group 은 바뀐 줄 묶음 [start, end). 빈 묶음(start == end)도 자리다.
struct Group {
    Flags& chg;
    size_t n, start = 0, end = 0;  // n 은 끝의 가짜 줄을 뺀 길이
    explicit Group(Flags& c) : chg(c), n(c.size() - 1) {
        while (end < n && chg[end]) ++end;
    }
    bool next() {
        if (end == n) return false;
        start = end = end + 1;
        while (end < n && chg[end]) ++end;
        return true;
    }
    bool previous() {
        if (start == 0) return false;
        end = start = start - 1;
        while (start > 0 && chg[start - 1]) --start;
        return true;
    }
    bool slide_down(const Lines& recs) {
        if (end >= n || recs[start] != recs[end]) return false;
        chg[start++] = false, chg[end++] = true;
        while (end < n && chg[end]) ++end;
        return true;
    }
    bool slide_up(const Lines& recs) {
        if (start == 0 || recs[start - 1] != recs[end - 1])
            return false;
        chg[--start] = true, chg[--end] = false;
        while (start > 0 && chg[start - 1]) --start;
        return true;
    }
};

// compact 는 한 쪽 파일의 바뀐 줄 묶음을 밀어 자리를 정한다(§11.2).
// 묶음마다 위로 끝까지, 다시 아래로 끝까지 민다(밀다가 이웃 묶음과
// 붙으면 처음부터). 상대 파일의 바뀐 묶음과 끝이 맞는 자리가
// 있었으면 그리로 되올리고, 없으면 맨 아래에 둔다. 상대 쪽 묶음 표지
// go 는 묶음과 발을 맞춰 움직인다. O(줄 수 × 미는 거리).
Flags compact(const Lines& recs, Flags rchg, Flags ochg) {
    rchg.push_back(false), ochg.push_back(false);
    Group g(rchg), go(ochg);
    for (;;) {
        if (g.end != g.start) {
            size_t size, earliest;
            long match_end;
            do {
                size = g.end - g.start;
                match_end = -1;
                while (g.slide_up(recs)) go.previous();
                earliest = g.end;
                if (go.end > go.start) match_end = long(g.end);
                while (g.slide_down(recs)) {
                    go.next();
                    if (go.end > go.start) match_end = long(g.end);
                }
            } while (size != g.end - g.start);
            if (g.end != earliest && match_end != -1)
                while (go.end == go.start)
                    g.slide_up(recs), go.previous();
        }
        if (!g.next()) break;
        go.next();
    }
    rchg.pop_back();
    return rchg;
}

std::string span(size_t start, size_t count) {
    auto first = std::to_string(count ? start + 1 : start);
    return count == 1 ? first : first + "," + std::to_string(count);
}

std::string rstrip(std::string s) {
    s.erase(s.find_last_not_of(" \t\n\r\v\f") + 1);
    return s;
}

// is_func 는 git 기본 드라이버의 함수 줄 — 첫 바이트가 영문자·'_'·'$'.
bool is_func(const std::string& line) {
    return !line.empty() && (std::isalpha(uint8_t(line[0])) ||
                             line[0] == '_' || line[0] == '$');
}
}  // namespace

// split_lines 는 바이트 → 줄 목록. 줄마다 '\n' 을 품고, 마지막 줄만
// 없을 수 있다.
Lines split_lines(std::string_view data) {
    Lines out;
    for (size_t a = 0; a < data.size();) {
        auto b = std::min(data.find('\n', a), data.size() - 1);
        out.emplace_back(data.substr(a, b - a + 1));
        a = b + 1;
    }
    return out;
}

// myers 는 1·2 단계 — 앞뒤를 깎고 가운데를 앞방향 Myers 로.
std::pair<Flags, Flags> myers(const Lines& a, const Lines& b) {
    size_t n = a.size(), m = b.size(), s = 0, e = 0;
    while (s < n && s < m && a[s] == b[s]) ++s;
    while (e < n - s && e < m - s && a[n - 1 - e] == b[m - 1 - e]) ++e;
    auto [ma, mb] = forward(Lines(a.begin() + s, a.end() - e),
                            Lines(b.begin() + s, b.end() - e));
    Flags ra(n), rb(m);
    std::copy(ma.begin(), ma.end(), ra.begin() + s);
    std::copy(mb.begin(), mb.end(), rb.begin() + s);
    return {ra, rb};
}

// edit_flags 는 세 단계를 다 거친 (ra, rb) — 계약의 전부(§11.2).
std::pair<Flags, Flags> edit_flags(const Lines& a, const Lines& b) {
    auto [ra, rb] = myers(a, b);
    ra = compact(a, ra, rb);
    rb = compact(b, rb, ra);
    return {ra, rb};
}

// build_changes 는 바뀐 곳들, 앞에서부터. 끝에서 앞으로 훑으며 같은
// 자리에서 만나는 지운 묶음과 끼운 묶음을 한 바뀐 곳으로 묶는다
// (git 의 xdl_build_script).
std::vector<Change> build_changes(const Flags& ra, const Flags& rb) {
    std::vector<Change> out;
    size_t i1 = ra.size(), i2 = rb.size();
    while (i1 > 0 || i2 > 0) {
        if ((i1 > 0 && ra[i1 - 1]) || (i2 > 0 && rb[i2 - 1])) {
            size_t l1 = i1, l2 = i2;
            while (i1 > 0 && ra[i1 - 1]) --i1;
            while (i2 > 0 && rb[i2 - 1]) --i2;
            out.push_back({i1, i2, l1 - i1, l2 - i2});
        } else {
            --i1, --i2;
        }
    }
    std::reverse(out.begin(), out.end());
    return out;
}

// unified_diff 는 덩어리들(SPEC.md §11.3). 같으면 "".
std::string unified_diff(const Lines& a, const Lines& b) {
    auto [ra, rb] = edit_flags(a, b);
    auto ch = build_changes(ra, rb);
    Lines out;
    for (size_t i = 0; i < ch.size();) {
        size_t j = i;
        while (j + 1 < ch.size() &&
               ch[j + 1].a - (ch[j].a + ch[j].na) <= 2 * context)
            ++j;
        size_t s1 = ch[i].a > context ? ch[i].a - context : 0;
        size_t s2 = ch[i].b > context ? ch[i].b - context : 0;
        size_t e1 = std::min(ch[j].a + ch[j].na + context, a.size());
        size_t e2 = std::min(ch[j].b + ch[j].nb + context, b.size());
        std::string func;
        for (size_t q = s1; q-- > 0;)
            if (is_func(a[q])) {
                func = " " + rstrip(rstrip(a[q]).substr(0, 80));
                break;
            }
        out.push_back("@@ -" + span(s1, e1 - s1) + " +" +
                      span(s2, e2 - s2) + " @@" + func + "\n");
        size_t p1 = s1;
        for (size_t k = i; k <= j; ++k) {
            for (size_t q = p1; q < ch[k].a; ++q)
                out.push_back(" " + a[q]);
            for (size_t q = 0; q < ch[k].na; ++q)
                out.push_back("-" + a[ch[k].a + q]);
            for (size_t q = 0; q < ch[k].nb; ++q)
                out.push_back("+" + b[ch[k].b + q]);
            p1 = ch[k].a + ch[k].na;
        }
        for (size_t q = p1; q < e1; ++q) out.push_back(" " + a[q]);
        i = j + 1;
    }
    std::string s;
    for (auto& line : out)
        s += line.ends_with("\n")
                 ? line
                 : line + "\n\\ No newline at end of file\n";
    return s;
}

// file_diff 는 파일 하나의 diff 전체(SPEC.md §11.4). old·now 가 없으면
// 새로 생김·지워짐. 같으면 "".
std::string file_diff(const std::string& path_a,
                      const std::string& path_b,
                      const std::optional<Side>& old,
                      const std::optional<Side>& now) {
    if (old && now && old->mode == now->mode && old->oid == now->oid)
        return "";
    auto qa = quote_path("a/" + path_a), qb = quote_path("b/" + path_b);
    auto mode = [](uint32_t m) {
        char buf[8];
        std::snprintf(buf, sizeof buf, "%06o", m);
        return std::string(buf);
    };
    std::string head = "diff --git " + qa + " " + qb + "\n";
    const std::string z = "0000000";
    if (!old) {
        head += "new file mode " + mode(now->mode) + "\nindex " + z +
                ".." + now->oid.substr(0, 7) + "\n";
    } else if (!now) {
        head += "deleted file mode " + mode(old->mode) + "\nindex " +
                old->oid.substr(0, 7) + ".." + z + "\n";
    } else {
        if (old->mode != now->mode)
            head += "old mode " + mode(old->mode) + "\nnew mode " +
                    mode(now->mode) + "\n";
        if (old->oid == now->oid) return head;  // 모드만 바뀜
        head += "index " + old->oid.substr(0, 7) + ".." +
                now->oid.substr(0, 7) +
                (old->mode == now->mode ? " " + mode(old->mode) : "") +
                "\n";
    }
    auto da = old ? old->data : "", db = now ? now->data : "";
    auto na = old ? qa : "/dev/null", nb = now ? qb : "/dev/null";
    if (da.substr(0, binary_probe).find('\0') != da.npos ||
        db.substr(0, binary_probe).find('\0') != db.npos)
        return head + "Binary files " + na + " and " + nb + " differ\n";
    return head + "--- " + na + "\n+++ " + nb + "\n" +
           unified_diff(split_lines(da), split_lines(db));
}

// blob_side 는 저장소의 blob 에서 한 쪽을 만든다.
Side blob_side(const std::string& gitdir, const Blob& b) {
    return {b.mode, b.oid, read_object(gitdir, b.oid).body};
}

// disk_side 는 디스크의 파일에서 한 쪽을 만든다. 없으면 nullopt.
std::optional<Side> disk_side(const std::string& path) {
    struct stat st;
    if (::stat(path.c_str(), &st) != 0 || !S_ISREG(st.st_mode))
        return std::nullopt;
    auto data = try_read(path);
    if (!data) return std::nullopt;
    return Side{st.st_mode & 0100 ? 0100755u : 0100644u,
                hash_object("blob", *data), *data};
}
}  // namespace mygit
