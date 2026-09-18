// mygit — C++ 구현의 선언 전부 (SPEC.md). 모듈마다 .cpp 하나.
#pragma once
#include <array>
#include <cstdint>
#include <stdexcept>
#include <string>
#include <string_view>

namespace mygit {

inline constexpr int STEP = 1;

// 명령이 멈추는 까닭. code 는 종료 코드(SPEC.md §1.4).
struct GitError : std::runtime_error {
    int code;
    explicit GitError(const std::string& msg, int c = 128)
        : std::runtime_error(msg), code(c) {}
};
[[noreturn]] inline void not_implemented() {
    throw GitError("not implemented", 99);
}

// ── sha1.cpp (SPEC.md §2) ─────────────────────────────────────────
class Sha1 {
   public:
    Sha1();
    Sha1& update(std::string_view data);
    std::array<uint8_t, 20> digest() const;

   private:
    uint32_t h_[5];
    std::string buf_;
    uint64_t n_ = 0;
};
std::string sha1_raw(std::string_view data);
std::string sha1_hex(std::string_view data);
std::string to_hex(std::string_view raw);
std::string from_hex(std::string_view hex);

}  // namespace mygit
