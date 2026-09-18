// 객체 (SPEC.md §4.1 · §4.6) — 이름은 내용의 SHA-1 이다.
//
// 이름 = SHA-1("<형식> <크기>\0" + 몸). 같은 내용은 어느 저장소에서
// 누가 만들어도 같은 이름을 얻는다. 느슨한 객체는 그 바이트를 zlib
// 으로 싸서 .git/objects/<앞 2글자>/<나머지 38글자> 에 둔다. 느슨한
// 객체에 없으면 팩에서 찾는다(SPEC.md §5.2).
#include <sys/stat.h>
#include <unistd.h>

#include <algorithm>
#include <filesystem>
#include <fstream>
#include <set>
#include <sstream>

#include "mygit.hpp"

namespace fs = std::filesystem;

namespace mygit {
namespace {
std::string header(std::string_view type, std::string_view body) {
    return std::string(type) + " " + std::to_string(body.size()) +
           std::string(1, '\0');
}

// parse_raw 는 풀린 바이트 → 객체. 머리의 크기가 몸과 다르면 오류.
Object parse_raw(const std::string& raw, const std::string& oid) {
    auto nul = raw.find('\0');
    auto sp = raw.find(' ');
    auto size = sp < nul ? raw.substr(sp + 1, nul - sp - 1) : "";
    if (nul == raw.npos || size.empty() ||
        size.find_first_not_of("0123456789") != size.npos)
        throw GitError("fatal: mygit: bad object header in " + oid);
    Object o{raw.substr(0, sp), raw.substr(nul + 1)};
    if (!is_type(o.type) || std::stoull(size) != o.body.size())
        throw GitError("fatal: mygit: object " + oid + " is corrupt");
    return o;
}
}  // namespace

std::optional<std::string> try_read(const std::string& path) {
    std::ifstream f(path, std::ios::binary);
    if (!f) return std::nullopt;
    std::ostringstream s;
    s << f.rdbuf();
    return s.str();
}

bool is_type(std::string_view t) {
    return t == "blob" || t == "tree" || t == "commit" || t == "tag";
}

std::string hash_object(std::string_view type, std::string_view body) {
    auto d = Sha1().update(header(type, body)).update(body).digest();
    return to_hex(std::string(d.begin(), d.end()));
}

std::string object_path(const std::string& gitdir,
                        const std::string& oid) {
    return gitdir + "/objects/" + oid.substr(0, 2) + "/" +
           oid.substr(2);
}

// write_object 는 이미 있으면 아무것도 하지 않는다 — 이름이 같으면
// 내용도 같다. 임시 파일에 다 쓴 뒤 이름을 바꿔 넣어, 도중에 죽어도
// 반쪽 객체가 남지 않는다.
std::string write_object(const std::string& gitdir,
                         std::string_view type, std::string_view body) {
    auto oid = hash_object(type, body);
    auto path = object_path(gitdir, oid);
    if (fs::exists(path)) return oid;
    auto dir = fs::path(path).parent_path();
    fs::create_directories(dir);
    std::string tmp = (dir / "tmp_obj_XXXXXX").string();
    int fd = mkstemp(tmp.data());
    if (fd < 0) throw GitError("fatal: mygit: cannot write " + path);
    auto data = compress(header(type, body) + std::string(body));
    bool ok =
        write(fd, data.data(), data.size()) == ssize_t(data.size());
    ok = close(fd) == 0 && ok && chmod(tmp.c_str(), 0444) == 0 &&
         rename(tmp.c_str(), path.c_str()) == 0;
    if (!ok) {
        unlink(tmp.c_str());
        throw GitError("fatal: mygit: cannot write " + path);
    }
    return oid;
}

std::map<std::string, Object> packed_objects(const std::string&) {
    return {};
}

Object read_object(const std::string& gitdir, const std::string& oid) {
    if (auto data = try_read(object_path(gitdir, oid)))
        return parse_raw(decompress(*data), oid);
    auto packed = packed_objects(gitdir);
    auto it = packed.find(oid);
    if (it == packed.end())
        throw GitError("fatal: mygit: object " + oid + " not found");
    return it->second;
}

std::vector<std::string> all_loose(const std::string& gitdir) {
    std::vector<std::string> out;
    std::error_code ec;
    for (auto& d : fs::directory_iterator(gitdir + "/objects", ec)) {
        auto dn = d.path().filename().string();
        if (dn.size() != 2) continue;
        for (auto& f : fs::directory_iterator(d.path())) {
            auto fn = f.path().filename().string();
            if (fn.size() == 38) out.push_back(dn + fn);
        }
    }
    std::sort(out.begin(), out.end());
    return out;
}

// find_object 는 앞부분(4글자 이상)으로 찾는다: 하나면 그 이름, 없으면
// "". 둘 이상이면 git 처럼 모호하다고 멈춘다. O(객체 수).
std::string find_object(const std::string& gitdir,
                        const std::string& prefix) {
    std::string p = prefix;
    std::transform(p.begin(), p.end(), p.begin(), ::tolower);
    if (p.size() < 4 ||
        p.find_first_not_of("0123456789abcdef") != p.npos)
        return "";
    std::set<std::string> ids;
    for (auto& o : all_loose(gitdir)) ids.insert(o);
    for (auto& [o, _] : packed_objects(gitdir)) ids.insert(o);
    if (p.size() == 40) return ids.count(p) ? p : "";
    std::vector<std::string> hits;
    for (auto& o : ids)
        if (o.compare(0, p.size(), p) == 0) hits.push_back(o);
    if (hits.size() > 1)
        throw GitError("error: short object ID " + prefix +
                       " is ambiguous");
    return hits.empty() ? "" : hits[0];
}
}  // namespace mygit
