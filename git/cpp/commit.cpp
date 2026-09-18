// commit·tag 객체와 신원 줄 (SPEC.md §4.4 · §4.5 · §1.3 · §9.1).
//
// 커밋 = 트리 하나 + 부모 목록 + 누가·언제 + 메시지. 커밋의 이름에는
// 작성 시각과 시간대까지 들어가므로, 같은 트리라도 1초만 달라도 다른
// 커밋이다 — 그래서 mygit 은 시계를 읽지 않고 환경 변수만 믿는다.
#include <cstdio>
#include <regex>
#include <sstream>

#include "mygit.hpp"

namespace mygit {
namespace {
const char* days[] = {"Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"};
const char* months[] = {"Jan", "Feb", "Mar", "Apr", "May", "Jun",
                        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"};

long long floor_div(long long a, long long b) {
    return a / b - (a % b != 0 && (a < 0) != (b < 0));
}

// civil_from_days 는 1970-01-01 부터의 날 수 → (해, 달, 일). Howard
// Hinnant 의 그레고리력 공식 — 표준 달력 함수를 쓰지 않는다. O(1).
void civil_from_days(long long z, long long& y, int& m, int& d) {
    z += 719468;
    long long era = floor_div(z, 146097), doe = z - era * 146097;
    long long yoe =
        (doe - doe / 1460 + doe / 36524 - doe / 146096) / 365;
    long long doy = doe - (365 * yoe + yoe / 4 - yoe / 100);
    long long mp = (5 * doy + 2) / 153;
    d = int(doy - (153 * mp + 2) / 5 + 1);
    m = int(mp < 10 ? mp + 3 : mp - 9);
    y = yoe + era * 400 + (m <= 2);
}

std::string rstrip(std::string s) {
    s.erase(s.find_last_not_of(" \t\r\v\f") + 1);
    return s;
}

std::vector<std::string> lines_of(const std::string& text) {
    std::vector<std::string> out;
    size_t a = 0;
    for (size_t b; (b = text.find('\n', a)) != text.npos; a = b + 1)
        out.push_back(text.substr(a, b - a));
    out.push_back(text.substr(a));
    return out;
}
}  // namespace

// parse_ident 는 '이름 <메일> 초 ±hhmm' → Ident.
Ident parse_ident(const std::string& line) {
    static const std::regex re(R"(^(.*) <(.*)> (-?\d+) ([+-]\d{4})$)");
    std::smatch m;
    if (!std::regex_match(line, m, re))
        throw GitError("fatal: mygit: bad ident line: " + line);
    return {m[1], m[2], std::stoll(m[3]), m[4]};
}

// ident_from_env 는 GIT_<who>_NAME·EMAIL·DATE → 신원 줄(SPEC.md
// §1.3). 설정 파일도 시계도 보지 않는다 — 캡처가 세 번 같으려면
// 입력이 전부 드러나 있어야 하기 때문이다.
std::string ident_from_env(const Env& env, const std::string& who) {
    std::string vals[3];
    const char* parts[] = {"NAME", "EMAIL", "DATE"};
    for (int i = 0; i < 3; ++i) {
        auto key = "GIT_" + who + "_" + parts[i];
        auto it = env.find(key);
        if (it == env.end())
            throw GitError("fatal: mygit: " + key + " is not set");
        vals[i] = it->second;
    }
    static const std::regex date(R"(^\d+ [+-]\d{4}$)");
    if (!std::regex_match(vals[2], date))
        throw GitError("fatal: mygit: GIT_" + who +
                       "_DATE is not '<seconds> <+hhmm>'");
    return vals[0] + " <" + vals[1] + "> " + vals[2];
}

// format_date 는 git log 의 Date 꼴 — 'Wed Nov 15 07:13:20 2023
// +0900'. 시각을 그 시간대로 옮겨 찍는다. 일은 앞에 0 을 붙이지 않는다.
std::string format_date(long long secs, const std::string& tz) {
    int off = std::stoi(tz.substr(1, 2)) * 3600 +
              std::stoi(tz.substr(3, 2)) * 60;
    long long local = secs + (tz[0] == '-' ? -off : off);
    long long dn = floor_div(local, 86400), rest = local - dn * 86400;
    long long y;
    int m, d;
    civil_from_days(dn, y, m, d);
    char buf[64];
    std::snprintf(buf, sizeof buf,
                  "%s %s %d %02lld:%02lld:%02lld %lld ",
                  days[((dn % 7) + 11) % 7], months[m - 1], d,
                  rest / 3600, rest / 60 % 60, rest % 60, y);
    return buf + tz;
}

// cleanup_message 는 commit -m 의 공백 정리(cleanup=whitespace). 줄마다
// 끝 공백을 지우고, 이어진 빈 줄은 하나로, 앞뒤의 빈 줄은 지운다.
// 줄 앞의 공백은 남긴다.
std::string cleanup_message(const std::string& text) {
    std::vector<std::string> out;
    for (auto& raw : lines_of(text)) {
        auto line = rstrip(raw);
        if (!line.empty() || (!out.empty() && !out.back().empty()))
            out.push_back(line);
    }
    while (!out.empty() && out.back().empty()) out.pop_back();
    std::string s;
    for (auto& l : out) s += l + "\n";
    return s;
}

// subject_of 는 첫 문단의 줄들을 공백 하나로 이은 것(SPEC.md §4.4).
// 줄 끝의 공백은 떼지만 앞의 공백은 남긴다.
std::string subject_of(const std::string& message) {
    std::string out;
    for (auto& line : lines_of(message)) {
        if (line.find_first_not_of(" \t\r\v\f") == line.npos) break;
        out += (out.empty() ? "" : " ") + rstrip(line);
    }
    return out;
}

// parse_commit 은 커밋 몸 → Commit. 모르는 머리 줄(gpgsig·mergetag 와
// 그 이어진 줄)은 건너뛴다.
Commit parse_commit(std::string_view body) {
    auto split = body.find("\n\n");
    Commit c;
    if (split != body.npos) c.message = body.substr(split + 2);
    for (auto& line : lines_of(std::string(body.substr(0, split)))) {
        auto sp = line.find(' ');
        auto key = line.substr(0, sp), val = line.substr(sp + 1);
        if (key == "tree")
            c.tree = val;
        else if (key == "parent")
            c.parents.push_back(val);
        else if (key == "author")
            c.author = val;
        else if (key == "committer")
            c.committer = val;
    }
    if (c.tree.empty() || c.committer.empty())
        throw GitError("fatal: mygit: corrupt commit object");
    return c;
}

std::string serialize_commit(const Commit& c) {
    std::string s = "tree " + c.tree + "\n";
    for (auto& p : c.parents) s += "parent " + p + "\n";
    return s + "author " + c.author + "\ncommitter " + c.committer +
           "\n\n" + c.message;
}

std::string serialize_tag(const std::string& obj,
                          const std::string& type,
                          const std::string& name,
                          const std::string& tagger,
                          const std::string& message) {
    return "object " + obj + "\ntype " + type + "\ntag " + name +
           "\ntagger " + tagger + "\n\n" + message;
}
}  // namespace mygit
