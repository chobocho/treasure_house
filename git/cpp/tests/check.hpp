// 시험 틀 — 외부 라이브러리 없이 TEST · CHECK · CHECK_EQ 셋만.
// 시험 파일 하나가 실행 파일 하나다(Makefile 의 test-cpp). 껍데기가
// 던지는 코드 99 는 "아직 없음" 이라 실패로 센다 — 거짓 초록을 막는다.
#pragma once
#include <iostream>
#include <string>
#include <vector>

#include "mygit.hpp"

namespace check {
struct Case {
    const char* name;
    void (*fn)();
};
inline std::vector<Case>& cases() {
    static std::vector<Case> v;
    return v;
}
struct Reg {
    Reg(const char* n, void (*f)()) { cases().push_back({n, f}); }
};
struct Skip {
    std::string why;
};
inline int failed = 0;
inline void expect(bool ok, const std::string& what, const char* file,
                   int line) {
    if (!ok) {
        ++failed;
        std::cerr << file << ":" << line << ": " << what << "\n";
    }
}
}  // namespace check

#define TEST(name)                             \
    static void name();                        \
    static check::Reg reg_##name(#name, name); \
    static void name()
#define CHECK(c) check::expect((c), #c, __FILE__, __LINE__)
#define CHECK_EQ(a, b) \
    check::expect((a) == (b), #a " == " #b, __FILE__, __LINE__)

int main() {
    int skipped = 0;
    for (auto& c : check::cases()) {
        try {
            c.fn();
        } catch (const check::Skip& s) {
            ++skipped;
            std::cerr << c.name << ": 건너뜀 — " << s.why << "\n";
        } catch (const mygit::GitError& e) {
            ++check::failed;
            std::cerr << c.name << ": GitError(" << e.code << ") "
                      << e.what() << "\n";
        } catch (const std::exception& e) {
            ++check::failed;
            std::cerr << c.name << ": " << e.what() << "\n";
        }
    }
    std::cout << check::cases().size() << " tests, " << check::failed
              << " failures, " << skipped << " skipped\n";
    return check::failed ? 1 : 0;
}
