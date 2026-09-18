// 작업 트리 (SPEC.md §8) — 경로 따옴표, 훑기, status.
#include <cstdio>

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
}  // namespace mygit
