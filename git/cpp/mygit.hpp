// mygit — C++ 구현의 선언 전부 (SPEC.md). 모듈마다 .cpp 하나.
#pragma once
#include <array>
#include <cstdint>
#include <map>
#include <optional>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace mygit {

inline constexpr int STEP = 3;

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

// ── inflate.cpp · deflate.cpp (SPEC.md §3) ─────────────────────────
std::string compress(std::string_view data);
std::string decompress(std::string_view data);
std::pair<std::string, size_t> decompress_prefix(std::string_view data,
                                                 size_t start);
uint32_t adler32(std::string_view data);
uint32_t crc32(std::string_view data);

// ── objects.cpp (SPEC.md §4.1 · §4.6) ─────────────────────────────
struct Object {
    std::string type, body;
};
// 파일 전부 — 없거나 못 읽으면 nullopt.
std::optional<std::string> try_read(const std::string& path);
// 팩 안 객체 전부 {이름: 객체} — 11단계 전에는 빈 것.
std::map<std::string, Object> packed_objects(const std::string& gitdir);
bool is_type(std::string_view type);
std::string hash_object(std::string_view type, std::string_view body);
std::string object_path(const std::string& gitdir,
                        const std::string& oid);
std::string write_object(const std::string& gitdir,
                         std::string_view type, std::string_view body);
Object read_object(const std::string& gitdir, const std::string& oid);
std::vector<std::string> all_loose(const std::string& gitdir);
std::string find_object(const std::string& gitdir,
                        const std::string& prefix);

// ── cli.cpp (SPEC.md §1 · §9) ─────────────────────────────────────
using Env = std::map<std::string, std::string>;
struct Result {
    int code;
    std::string out, err;
};
Env os_env();
// 명령 하나를 돌린다. input 이 nullopt 면 진짜 표준 입력을 읽는다.
Result run(const std::vector<std::string>& args, const std::string& cwd,
           const Env& env, std::optional<std::string> input);

}  // namespace mygit
