// 인덱스 (SPEC.md §7) — .git/index, 다음 커밋이 될 트리의 초안.
//
// 작업 트리와 저장소 사이의 이 파일 하나가 "스테이징" 의 실체다.
// 항목마다 경로·모드·blob 이름과 함께 파일의 stat 칸(시각·크기·
// inode)을 적어 두는데, git 은 그것으로 "안 바뀐 파일" 을 해시 없이
// 가려낸다. mygit 은 칸을 채워 두기만 하고 자신은 믿지 않는다(§7.2).
// 판 2 로 쓰고, 판 2·3 을 읽는다. 확장은 읽을 때 건너뛴다. 수는 전부
// 빅 엔디언.
#include <fcntl.h>
#include <sys/stat.h>
#include <unistd.h>

#include <algorithm>

#include "mygit.hpp"

namespace mygit {
namespace {
uint32_t be32(std::string_view d, size_t p) {
    return uint32_t(uint8_t(d[p])) << 24 |
           uint32_t(uint8_t(d[p + 1])) << 16 |
           uint32_t(uint8_t(d[p + 2])) << 8 | uint8_t(d[p + 3]);
}
void put32(std::string& out, uint32_t v) {
    for (int k = 3; k >= 0; --k) out += char(v >> (8 * k));
}
}  // namespace

IndexEntry index_entry(const std::string& path, const std::string& oid,
                       uint32_t mode, int stage) {
    IndexEntry e;
    e.path = path, e.oid = oid, e.mode = mode, e.stage = stage;
    return e;
}

// entry_from_stat 는 작업 트리 파일의 stat 으로 항목을 채운다(§7.2).
// 모드는 소유자 실행 비트만 본다 — git 과 같다. 칸은 32비트로 자른다.
IndexEntry entry_from_stat(const std::string& path,
                           const std::string& abspath,
                           const std::string& oid) {
    struct stat st;
    if (::stat(abspath.c_str(), &st) != 0)
        throw GitError("fatal: mygit: cannot stat " + abspath);
    auto e =
        index_entry(path, oid, st.st_mode & 0100 ? 0100755 : 0100644);
    e.size = uint32_t(st.st_size);
    e.ctime_s = uint32_t(st.st_ctim.tv_sec);
    e.ctime_ns = uint32_t(st.st_ctim.tv_nsec);
    e.mtime_s = uint32_t(st.st_mtim.tv_sec);
    e.mtime_ns = uint32_t(st.st_mtim.tv_nsec);
    e.dev = uint32_t(st.st_dev), e.ino = uint32_t(st.st_ino);
    e.uid = st.st_uid, e.gid = st.st_gid;
    return e;
}

// parse_index 는 인덱스 바이트 → 항목들. 끝 SHA-1 이 틀리면 오류.
// 판 3 은 flags 의 비트 14 가 서 있는 항목 뒤에 2바이트 확장 flags 가
// 더 있다(skip-worktree 가 거기 산다). O(파일 크기).
std::vector<IndexEntry> parse_index(std::string_view data) {
    const GitError corrupt("fatal: mygit: index file corrupt");
    if (data.size() < 32 || data.substr(0, 4) != "DIRC") throw corrupt;
    if (sha1_raw(data.substr(0, data.size() - 20)) !=
        data.substr(data.size() - 20))
        throw corrupt;
    uint32_t ver = be32(data, 4), count = be32(data, 8);
    if (ver == 4) throw GitError("fatal: mygit: index v4 unsupported");
    if (ver != 2 && ver != 3)
        throw GitError("fatal: mygit: index version " +
                       std::to_string(ver));
    std::vector<IndexEntry> out;
    size_t pos = 12;
    for (uint32_t i = 0; i < count; ++i) {
        if (pos + 62 > data.size() - 20) throw corrupt;
        IndexEntry e;
        uint32_t* f[] = {
            &e.ctime_s, &e.ctime_ns, &e.mtime_s, &e.mtime_ns, &e.dev,
            &e.ino,     &e.mode,     &e.uid,     &e.gid,      &e.size};
        for (int k = 0; k < 10; ++k) *f[k] = be32(data, pos + 4 * k);
        e.oid = to_hex(data.substr(pos + 40, 20));
        unsigned flags =
            uint8_t(data[pos + 60]) << 8 | uint8_t(data[pos + 61]);
        e.stage = (flags >> 12) & 3;
        e.assume_valid = flags & 0x8000;
        size_t start = pos + 62;
        if (flags & 0x4000) {  // 판 3 의 확장 flags
            e.skip_worktree = uint8_t(data[start]) & 0x40;
            start += 2;
        }
        // 이름 길이가 0xfff 를 넘어도 NUL 까지 읽는다
        auto end = data.find('\0', start);
        if (end == data.npos) throw corrupt;
        e.path = data.substr(start, end - start);
        pos += (start - pos + e.path.size() + 8) / 8 * 8;
        out.push_back(e);
    }
    return out;
}

// serialize_index 는 항목들 → 판 2 인덱스 바이트. 경로·단계 차례로
// 정렬한다. 항목 길이 = (62 + 이름 길이 + 8) & ~7 — NUL 이 1‥8 개.
// 판 2 에는 확장 flags 가 없으므로 skip-worktree 는 여기서 사라진다.
std::string serialize_index(std::vector<IndexEntry> ents) {
    std::sort(ents.begin(), ents.end(), [](auto& a, auto& b) {
        return std::tie(a.path, a.stage) < std::tie(b.path, b.stage);
    });
    std::string out = "DIRC";
    put32(out, 2);
    put32(out, uint32_t(ents.size()));
    for (auto& e : ents) {
        size_t start = out.size();
        for (auto v : {e.ctime_s, e.ctime_ns, e.mtime_s, e.mtime_ns,
                       e.dev, e.ino, e.mode, e.uid, e.gid, e.size})
            put32(out, v);
        out += from_hex(e.oid);
        unsigned flags =
            unsigned(e.stage) << 12 |
            unsigned(std::min<size_t>(e.path.size(), 0xfff)) |
            (e.assume_valid ? 0x8000 : 0);
        out += char(flags >> 8), out += char(flags);
        out += e.path;
        out.append(8 - (out.size() - start) % 8, '\0');
    }
    return out + sha1_raw(out);
}

// read_index 는 .git/index 를 읽는다. 없으면(첫 add 전) 빈 목록.
std::vector<IndexEntry> read_index(const std::string& gitdir) {
    auto data = try_read(gitdir + "/index");
    return data ? parse_index(*data) : std::vector<IndexEntry>{};
}

// write_index 는 index.lock 에 쓰고 이름을 바꿔 넣는다(SPEC.md §7.4).
void write_index(const std::string& gitdir,
                 const std::vector<IndexEntry>& entries) {
    auto p = gitdir + "/index", lock = p + ".lock";
    int fd = open(lock.c_str(), O_WRONLY | O_CREAT | O_EXCL, 0666);
    if (fd < 0) throw GitError("fatal: mygit: unable to lock " + p);
    auto data = serialize_index(entries);
    bool ok =
        write(fd, data.data(), data.size()) == ssize_t(data.size());
    if (close(fd) != 0 || !ok || rename(lock.c_str(), p.c_str()) != 0)
        throw GitError("fatal: mygit: cannot write " + p);
}
}  // namespace mygit
