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

inline constexpr int STEP = 10;

// 명령이 멈추는 까닭. code 는 종료 코드(SPEC.md §1.4).
struct GitError : std::runtime_error {
    int code;
    explicit GitError(const std::string& msg, int c = 128)
        : std::runtime_error(msg), code(c) {}
};
[[noreturn]] inline void not_implemented() {
    throw GitError("not implemented", 99);
}
using Env = std::map<std::string, std::string>;

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

// ── tree.cpp (SPEC.md §4.3) ────────────────────────────────────────
inline const std::string DIR = "40000";
struct TreeEntry {
    std::string mode, name, oid;
    bool operator==(const TreeEntry&) const = default;
};
struct PathEntry {
    std::string mode, oid, path;
    bool operator==(const PathEntry&) const = default;
};
std::string tree_entry_key(const std::string& mode,
                           const std::string& name);
std::vector<TreeEntry> parse_tree(std::string_view body);
std::string serialize_tree(std::vector<TreeEntry> entries);
std::string write_tree(const std::string& gitdir,
                       const std::vector<PathEntry>& entries);
std::vector<PathEntry> flatten_tree(const std::string& gitdir,
                                    const std::string& oid,
                                    const std::string& prefix = "");
std::string type_of_mode(const std::string& mode);

// ── index.cpp (SPEC.md §7) ─────────────────────────────────────────
struct IndexEntry {
    std::string path, oid;
    uint32_t mode = 0, size = 0;
    int stage = 0;
    uint32_t ctime_s = 0, ctime_ns = 0, mtime_s = 0, mtime_ns = 0;
    uint32_t dev = 0, ino = 0, uid = 0, gid = 0;
    bool assume_valid = false, skip_worktree = false;
};
IndexEntry index_entry(const std::string& path, const std::string& oid,
                       uint32_t mode, int stage = 0);
IndexEntry entry_from_stat(const std::string& path,
                           const std::string& abspath,
                           const std::string& oid);
std::vector<IndexEntry> parse_index(std::string_view data);
std::string serialize_index(std::vector<IndexEntry> entries);
std::vector<IndexEntry> read_index(const std::string& gitdir);
void write_index(const std::string& gitdir,
                 const std::vector<IndexEntry>& entries);

// ── worktree.cpp (SPEC.md §8) ──────────────────────────────────────
std::string quote_path(std::string_view path, bool space = false);
// Blob 은 경로 하나의 (모드, 이름) — 트리·인덱스·디스크를 견줄 때의 값.
struct Blob {
    uint32_t mode;
    std::string oid;
    bool operator==(const Blob&) const = default;
};
using TreeMap = std::map<std::string, Blob>;
std::vector<std::string> walk_worktree(const std::string& root);
std::optional<Blob> file_state(const std::string& root,
                               const std::string& path);
TreeMap tree_map(const std::string& gitdir, const std::string& tree);
std::string head_tree(const std::string& gitdir);
std::vector<std::string> status(const std::string& root,
                                const std::string& gitdir);
void write_file(const std::string& root, const std::string& path,
                uint32_t mode, const std::string& data);
void remove_file(const std::string& root, const std::string& path);
void checkout_tree(const std::string& root, const std::string& gitdir,
                   const std::string& old_tree,
                   const std::string& new_tree);
std::vector<std::string> local_changes(const std::string& root,
                                       const std::string& gitdir,
                                       const std::string& head_tree);

// ── commit.cpp (SPEC.md §4.4 · §4.5 · §1.3 · §9.1) ────────────────
struct Ident {
    std::string name, mail;
    long long secs;
    std::string tz;
};
struct Commit {
    std::string tree;
    std::vector<std::string> parents;
    std::string author, committer, message;
};
Ident parse_ident(const std::string& line);
std::string ident_from_env(const Env& env, const std::string& who);
std::string format_date(long long secs, const std::string& tz);
std::string cleanup_message(const std::string& text);
std::string subject_of(const std::string& message);
Commit parse_commit(std::string_view body);
std::string serialize_commit(const Commit& c);
std::string serialize_tag(const std::string& obj,
                          const std::string& type,
                          const std::string& name,
                          const std::string& tagger,
                          const std::string& message);

// ── refs.cpp (SPEC.md §6) ──────────────────────────────────────────
inline const std::string ZERO(40, '0');
struct Ref {
    bool sym;
    std::string val;
};
struct NamedRef {
    std::string name, oid;
};
struct ReflogEntry {
    std::string old, now, ident, msg;
    bool operator==(const ReflogEntry&) const = default;
};
std::map<std::string, std::string> packed_refs(
    const std::string& gitdir);
std::optional<Ref> read_ref(const std::string& gitdir,
                            const std::string& name);
std::string resolve_ref(const std::string& gitdir, std::string name);
std::pair<std::string, std::string> read_head(
    const std::string& gitdir);
std::vector<NamedRef> list_refs(const std::string& gitdir,
                                const std::string& prefix = "refs/");
void append_reflog(const std::string& gitdir, const std::string& name,
                   const std::string& old, const std::string& now,
                   const std::string& ident, const std::string& msg);
std::vector<ReflogEntry> read_reflog(const std::string& gitdir,
                                     const std::string& name);
void update_ref(const std::string& gitdir, const std::string& name,
                const std::string& now, const std::string& old,
                const std::string& msg, const std::string& ident);
void set_head(const std::string& gitdir, const std::string& target);
std::string peel(const std::string& gitdir, std::string oid,
                 const std::string& want);
std::string rev_parse(const std::string& gitdir,
                      const std::string& spec);
bool valid_branch_name(const std::string& name);

// ── walk.cpp (SPEC.md §10) ─────────────────────────────────────────
std::vector<std::string> walk_log(
    const std::string& gitdir, const std::vector<std::string>& starts);
bool is_ancestor(const std::string& gitdir, const std::string& a,
                 const std::string& b);
std::vector<std::string> merge_bases(const std::string& gitdir,
                                     const std::string& a,
                                     const std::string& b);

// ── diff.cpp (SPEC.md §11) ─────────────────────────────────────────
using Lines = std::vector<std::string>;
using Flags = std::vector<bool>;
// Change 는 바뀐 곳 하나 — a·b 의 자리와 줄 수.
struct Change {
    size_t a, b, na, nb;
};
// Side 는 diff 의 한 쪽 — (모드, 이름, 바이트).
struct Side {
    uint32_t mode;
    std::string oid, data;
};
Lines split_lines(std::string_view data);
std::pair<Flags, Flags> myers(const Lines& a, const Lines& b);
std::pair<Flags, Flags> edit_flags(const Lines& a, const Lines& b);
std::vector<Change> build_changes(const Flags& ra, const Flags& rb);
std::string unified_diff(const Lines& a, const Lines& b);
std::string file_diff(const std::string& path_a,
                      const std::string& path_b,
                      const std::optional<Side>& old,
                      const std::optional<Side>& now);
Side blob_side(const std::string& gitdir, const Blob& b);
std::optional<Side> disk_side(const std::string& path);

// ── merge.cpp (SPEC.md §12) ────────────────────────────────────────
// MergeResult 는 경로 하나의 트리 합치기 결과. gone 이면 지움,
// conflict 면 text 가 표지 든 내용이고 stages 가 단계 1‥3.
struct MergeResult {
    bool gone = false, conflict = false;
    Blob blob{};
    std::string text;
    std::map<int, Blob> stages;
};
struct TreeMerge {
    std::map<std::string, MergeResult> result;
    std::vector<std::string> notes, conflicts;
};
std::pair<std::string, int> merge3(const std::string& base,
                                   const std::string& ours,
                                   const std::string& theirs,
                                   const std::string& label);
TreeMerge merge_trees(const std::string& gitdir, const TreeMap& base,
                      const TreeMap& ours, const TreeMap& theirs,
                      const std::string& label);

// ── cli.cpp (SPEC.md §1 · §9) ─────────────────────────────────────
struct Result {
    int code;
    std::string out, err;
};
Env os_env();
// 명령 하나를 돌린다. input 이 nullopt 면 진짜 표준 입력을 읽는다.
Result run(const std::vector<std::string>& args, const std::string& cwd,
           const Env& env, std::optional<std::string> input);

}  // namespace mygit
