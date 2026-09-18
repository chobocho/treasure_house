// 시험 도우미 — golden/ 을 읽고 재료를 바이트로 만든다(SPEC §2.1).
// golden 은 진짜 git 이 만든 기준 바이트다. 시험은 git 을 부르지 않고
// 이 파일들만 읽는다. 경로는 git/ 에서 도는 make test-cpp 기준.
#pragma once
#include <fstream>
#include <map>
#include <sstream>
#include <string>
#include <vector>

#include "check.hpp"

namespace golden {
inline const std::string dir = "golden";

inline std::string read(const std::string& rel) {
    std::ifstream f(dir + "/" + rel, std::ios::binary);
    if (!f) throw std::runtime_error("golden 없음: " + rel);
    std::ostringstream s;
    s << f.rdbuf();
    return s.str();
}

inline std::vector<std::string> split(const std::string& s, char sep) {
    std::vector<std::string> out;
    size_t a = 0;
    for (size_t b; (b = s.find(sep, a)) != std::string::npos; a = b + 1)
        out.push_back(s.substr(a, b - a));
    out.push_back(s.substr(a));
    return out;
}

using Row = std::map<std::string, std::string>;

// tsv 는 주석(#)과 머리 줄을 뺀 행들을 칸 이름 → 값으로.
inline std::vector<Row> tsv(const std::string& rel) {
    std::vector<std::string> head;
    std::vector<Row> rows;
    for (auto& line : split(read(rel), '\n')) {
        if (line.empty() || line[0] == '#') continue;
        auto cols = split(line, '\t');
        if (head.empty()) {
            head = cols;
            continue;
        }
        Row r;
        for (size_t i = 0; i < head.size() && i < cols.size(); ++i)
            r[head[i]] = cols[i];
        rows.push_back(r);
    }
    return rows;
}

// unescape 는 text: 재료의 \n \t \\ \" \xHH 를 푼다.
inline std::string unescape(const std::string& s) {
    std::string out;
    for (size_t i = 0; i < s.size(); ++i) {
        if (s[i] != '\\' || i + 1 >= s.size()) {
            out += s[i];
            continue;
        }
        char n = s[++i];
        if (n == 'x') {
            out += char(std::stoi(s.substr(i + 1, 2), nullptr, 16));
            i += 2;
        } else {
            out += n == 'n' ? '\n' : n == 't' ? '\t' : n;
        }
    }
    return out;
}

// make 는 재료 한 줄을 바이트로(SPEC §2.1 · §16.4).
inline std::string make(const std::string& r) {
    auto c = r.find(':');
    std::string kind = r.substr(0, c),
                arg = c == r.npos ? "" : r.substr(c + 1);
    if (kind == "empty") return "";
    if (kind == "text") return unescape(arg);
    if (kind == "repeat") {
        auto p = split(arg, ':');
        return std::string(std::stoul(p[1]),
                           char(std::stoi(p[0], nullptr, 16)));
    }
    if (kind == "counter") {
        std::string out(std::stoul(arg), '\0');
        for (size_t i = 0; i < out.size(); ++i) out[i] = char(i % 251);
        return out;
    }
    if (kind == "seq") {
        auto p = split(arg, ':');
        std::string out;
        for (int i = std::stoi(p[0]); i <= std::stoi(p[1]); ++i)
            out += std::to_string(i) + "\n";
        return out;
    }
    if (kind == "golden") return read(arg);
    throw std::runtime_error("모르는 재료: " + r);
}

// git_error 는 fn 이 진짜 GitError 를 던지는지 — 코드 99(껍데기)는
// 아니다.
template <class F>
mygit::GitError git_error(F fn) {
    try {
        fn();
    } catch (const mygit::GitError& e) {
        if (e.code == 99) throw;
        return e;
    }
    throw std::runtime_error("GitError 가 나지 않았다");
}
}  // namespace golden
