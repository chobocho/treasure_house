// 팩 (SPEC.md §13) — 객체 여럿을 한 파일에, 비슷한 것은 델타로.
//
// 느슨한 객체는 파일 하나에 객체 하나지만, 팩은 객체들을 이어 붙이고
// 비슷한 객체는 "바탕에서 여기를 복사, 여기에 이것을 끼움" 이라는
// 델타로 적는다. 색인(.idx)은 이름 → 팩 안 자리의 표다. 팩 끝
// 20바이트는 팩 전체의 SHA-1 이고, 그것이 곧 파일 이름이다.
#include <sys/stat.h>

#include <algorithm>
#include <filesystem>

#include "mygit.hpp"

namespace mygit {
namespace {
const char* type_names[] = {"", "commit", "tree", "blob", "tag"};
const int ofs_delta = 6, ref_delta = 7;

uint8_t at(std::string_view d, size_t p) {
    return uint8_t(d[p]);
}

uint64_t be(std::string_view d, size_t p, int n) {
    uint64_t v = 0;
    for (int k = 0; k < n; ++k) v = v << 8 | at(d, p + k);
    return v;
}
void put_be(std::string& out, uint64_t v, int n) {
    for (int k = n - 1; k >= 0; --k) out += char(v >> (8 * k));
}

// varint_le 는 7비트씩 작은 쪽부터(델타 머리의 크기).
size_t varint_le(std::string_view d, size_t& pos) {
    size_t val = 0;
    for (int shift = 0;; shift += 7) {
        uint8_t b = at(d, pos++);
        val |= size_t(b & 0x7f) << shift;
        if (!(b & 0x80)) return val;
    }
}

std::string varint_out(size_t n) {
    std::string out;
    for (; n >= 0x80; n >>= 7) out += char((n & 0x7f) | 0x80);
    return out + char(n);
}

// resolve 는 델타 사슬을 풀어 형식·몸·이름·깊이를 채운다. 바탕이
// 뒤에 있을 수 있어(REF_DELTA) 되살릴 것이 줄지 않을 때까지
// 되풀이한다. O(항목 수 × 사슬 깊이) 최악.
void resolve(std::vector<PackEntry>& ents, const External& external) {
    std::map<size_t, PackEntry*> by_off;
    std::map<std::string, PackEntry*> by_oid;
    std::vector<PackEntry*> pending;
    for (auto& e : ents) {
        by_off[e.offset] = &e;
        if (e.type.empty()) {
            pending.push_back(&e);
        } else {
            e.oid = hash_object(e.type, e.body);
            by_oid[e.oid] = &e;
        }
    }
    while (!pending.empty()) {
        std::vector<PackEntry*> left;
        for (auto* e : pending) {
            PackEntry* b = nullptr;
            if (e->base_offset >= 0) {
                if (!by_off.count(size_t(e->base_offset)))
                    throw GitError("fatal: mygit: bad OFS_DELTA base");
                b = by_off[size_t(e->base_offset)];
            } else if (by_oid.count(e->base)) {
                b = by_oid[e->base];
            } else if (external) {
                auto o = external(e->base);
                e->type = o.type, e->depth = 1;
                e->body = apply_delta(o.body, *e->delta);
                e->oid = hash_object(e->type, e->body);
                by_oid[e->oid] = e;
                continue;
            }
            if (!b || b->type.empty()) {
                left.push_back(e);
                continue;
            }
            e->type = b->type;
            e->body = apply_delta(b->body, *e->delta);
            e->depth = b->depth + 1, e->base = b->oid;
            e->oid = hash_object(e->type, e->body);
            by_oid[e->oid] = e;
        }
        if (left.size() == pending.size())
            throw GitError("fatal: mygit: unresolved delta base");
        pending = left;
    }
}

// copy_op 은 복사 명령 — 0 이 아닌 바이트만 쓴다. 길이 0x10000 은
// 길이 바이트 없이.
std::string copy_op(size_t off, size_t n) {
    uint8_t op = 0x80;
    std::string tail;
    for (int k = 0; k < 4; ++k)
        if (uint8_t b = uint8_t(off >> (8 * k)))
            op |= 1 << k, tail += char(b);
    if (n != 0x10000)
        for (int k = 0; k < 3; ++k)
            if (uint8_t b = uint8_t(n >> (8 * k)))
                op |= 0x10 << k, tail += char(b);
    return char(op) + tail;
}

std::string entry_head(int type, size_t size) {
    std::string out;
    uint8_t b = uint8_t(type << 4 | (size & 15));
    for (size >>= 4; size; size >>= 7) {
        out += char(b | 0x80);
        b = uint8_t(size & 0x7f);
    }
    return out + char(b);
}

// ofs_out 은 OFS_DELTA 거리 — 큰 쪽부터, 이어지는 바이트마다 1 을 뺀다.
std::string ofs_out(size_t n) {
    std::string out(1, char(n & 0x7f));
    for (n >>= 7; n; n >>= 7)
        out.insert(out.begin(), char(0x80 | (--n & 0x7f)));
    return out;
}
}  // namespace

// apply_delta 는 델타를 바탕에 적용한다(SPEC.md §13.1). O(결과 길이).
std::string apply_delta(std::string_view base, std::string_view delta) {
    size_t pos = 0;
    if (varint_le(delta, pos) != base.size())
        throw GitError("fatal: mygit: delta base size mismatch");
    size_t want = varint_le(delta, pos);
    std::string out;
    while (pos < delta.size()) {
        uint8_t op = at(delta, pos++);
        if (op & 0x80) {  // 복사
            size_t off = 0, n = 0;
            for (int k = 0; k < 4; ++k)
                if (op & (1 << k))
                    off |= size_t(at(delta, pos++)) << (8 * k);
            for (int k = 0; k < 3; ++k)
                if (op & (0x10 << k))
                    n |= size_t(at(delta, pos++)) << (8 * k);
            if (!n) n = 0x10000;
            if (off + n > base.size())
                throw GitError("fatal: mygit: delta copy out of range");
            out.append(base.substr(off, n));
        } else if (op) {  // 끼움
            out.append(delta.substr(pos, op));
            pos += op;
        } else {
            throw GitError("fatal: mygit: delta opcode 0 is reserved");
        }
    }
    if (out.size() != want)
        throw GitError("fatal: mygit: delta result size mismatch");
    return out;
}

// read_pack 은 팩 바이트 → 항목들, 자리 차례. 앞에서부터 읽으며 zlib
// 스트림이 먹은 바이트 수로 다음 항목을 찾고, 델타는 바탕을 먼저
// 되살린 뒤 적용한다. O(팩 크기 + 되살린 크기).
std::vector<PackEntry> read_pack(std::string_view data,
                                 const External& external) {
    if (data.size() < 32 || data.substr(0, 4) != "PACK")
        throw GitError("fatal: mygit: not a pack file");
    if (sha1_raw(data.substr(0, data.size() - 20)) !=
        data.substr(data.size() - 20))
        throw GitError("fatal: mygit: pack checksum mismatch");
    auto ver = be(data, 4, 4), count = be(data, 8, 4);
    if (ver != 2 && ver != 3)
        throw GitError("fatal: mygit: pack version " +
                       std::to_string(ver));
    std::vector<PackEntry> ents;
    size_t pos = 12;
    for (uint64_t i = 0; i < count; ++i) {
        PackEntry e;
        e.offset = pos;
        // 머리: 첫 바이트의 낮은 4비트가 크기의 시작, 이어지는 바이트는
        // 7비트씩 위로 붙는다
        uint8_t b = at(data, pos++);
        e.packed_type = (b >> 4) & 7;
        size_t size = b & 15;
        for (int shift = 4; b & 0x80; shift += 7)
            b = at(data, pos++), size |= size_t(b & 0x7f) << shift;
        if (e.packed_type == ofs_delta) {
            // 거리 — 큰 쪽부터, 이어지는 바이트마다 +1
            b = at(data, pos++);
            size_t n = b & 0x7f;
            while (b & 0x80)
                b = at(data, pos++), n = (n + 1) << 7 | (b & 0x7f);
            e.base_offset = long(e.offset) - long(n);
        } else if (e.packed_type == ref_delta) {
            e.base = to_hex(data.substr(pos, 20));
            pos += 20;
        } else if (e.packed_type < 1 || e.packed_type > 4) {
            throw GitError("fatal: mygit: bad pack entry type " +
                           std::to_string(e.packed_type));
        }
        auto [raw, used] = decompress_prefix(data, pos);
        if (raw.size() != size)
            throw GitError("fatal: mygit: pack entry size mismatch");
        pos += used;
        e.end = pos;
        e.crc = crc32(data.substr(e.offset, pos - e.offset));
        if (e.packed_type <= 4)
            e.type = type_names[e.packed_type], e.body = raw;
        else
            e.delta = raw;
        ents.push_back(std::move(e));
    }
    if (pos != data.size() - 20)
        throw GitError("fatal: mygit: pack has trailing garbage");
    resolve(ents, external);
    return ents;
}

// read_idx 는 색인 판 2 → (항목들, 팩 체크섬 20바이트).
std::pair<std::vector<IdxEntry>, std::string> read_idx(
    std::string_view d) {
    if (d.size() < 8 + 256 * 4 + 40 ||
        d.substr(0, 8) != std::string_view("\xfftOc\0\0\0\2", 8))
        throw GitError("fatal: mygit: not a version 2 pack index");
    if (sha1_raw(d.substr(0, d.size() - 20)) != d.substr(d.size() - 20))
        throw GitError("fatal: mygit: pack index checksum mismatch");
    size_t n = be(d, 8 + 255 * 4, 4), p = 8 + 256 * 4;
    std::vector<IdxEntry> out(n);
    for (size_t k = 0; k < n; ++k) {
        out[k].oid = to_hex(d.substr(p + 20 * k, 20));
        out[k].crc = uint32_t(be(d, p + 20 * n + 4 * k, 4));
        auto v = be(d, p + 24 * n + 4 * k, 4);
        // 2 GiB 넘는 자리는 뒤의 8바이트 표에서
        out[k].offset =
            v & 0x80000000 ? be(d, p + 28 * n + 8 * (v & 0x7fffffff), 8)
                           : v;
    }
    return {out, std::string(d.substr(d.size() - 40, 20))};
}

// write_idx 는 항목들 → 색인 판 2 바이트(SPEC.md §13.2). 이름 차례로
// 정렬한 fanout·이름·CRC·자리, 팩 체크섬, 그 앞 전부의 SHA-1. 같은
// 팩이면 git 의 .idx 와 바이트까지 같다.
std::string write_idx(std::vector<PackEntry> ents,
                      const std::string& pack_sum) {
    std::sort(ents.begin(), ents.end(),
              [](auto& a, auto& b) { return a.oid < b.oid; });
    uint32_t fan[256] = {};
    for (auto& e : ents)
        fan[std::stoi(e.oid.substr(0, 2), nullptr, 16)]++;
    for (int k = 1; k < 256; ++k) fan[k] += fan[k - 1];
    std::string out("\xfftOc", 4);
    put_be(out, 2, 4);
    for (auto f : fan) put_be(out, f, 4);
    for (auto& e : ents) out += from_hex(e.oid);
    for (auto& e : ents) put_be(out, e.crc, 4);
    std::vector<uint64_t> big;
    for (auto& e : ents) {
        if (e.offset < 0x80000000) {
            put_be(out, e.offset, 4);
        } else {
            put_be(out, 0x80000000 | big.size(), 4);
            big.push_back(e.offset);
        }
    }
    for (auto o : big) put_be(out, o, 8);
    out += pack_sum;
    return out + sha1_raw(out);
}

// make_delta 는 바탕 → 결과의 델타(SPEC.md §13.3). 다섯 언어가 같은
// 바이트를 낸다. 바탕을 16바이트 칸으로 잘라 "칸 내용 → 처음 나온
// 자리" 표를 만들고, 결과를 앞에서부터 훑으며 표에 있는 칸이면 앞으로
// 늘일 수 있는 만큼 복사, 없으면 한 바이트씩 끼울 것에 모은다.
// O(결과 길이 × 복사 길이) 최악.
std::string make_delta(std::string_view base, std::string_view target) {
    const size_t block = 16;
    std::map<std::string_view, size_t> table;
    for (size_t off = 0; off + block <= base.size(); off += block)
        table.emplace(base.substr(off, block),
                      off);  // 처음 것만 남는다
    auto out = varint_out(base.size()) + varint_out(target.size());
    std::string pend;
    auto flush = [&] {
        for (size_t k = 0; k < pend.size(); k += 127) {
            auto chunk = pend.substr(k, 127);
            out += char(chunk.size()) + chunk;
        }
        pend.clear();
    };
    for (size_t i = 0; i < target.size();) {
        auto hit = i + block <= target.size()
                       ? table.find(target.substr(i, block))
                       : table.end();
        if (hit == table.end()) {
            pend += target[i++];
            if (pend.size() == 127) flush();
            continue;
        }
        size_t o = hit->second, n = block;
        while (o + n < base.size() && i + n < target.size() &&
               base[o + n] == target[i + n])
            ++n;
        flush();
        for (size_t k = 0; k < n; k += 0x10000)
            out += copy_op(o + k, std::min<size_t>(0x10000, n - k));
        i += n;
    }
    flush();
    return out;
}

// write_pack 은 → (팩 바이트, 항목들). 압축은 저장 블록이라 다른
// 언어와 바이트가 다르지만, 풀린 바이트와 이름은 같다(SPEC.md §3.1).
std::pair<std::string, std::vector<PackEntry>> write_pack(
    const std::vector<PackItem>& items) {
    std::string out = "PACK";
    put_be(out, 2, 4);
    put_be(out, items.size(), 4);
    std::vector<PackEntry> ents;
    for (auto& it : items) {
        PackEntry e;
        e.offset = out.size(), e.type = it.type, e.body = it.body;
        e.oid = hash_object(it.type, it.body);
        std::string raw = it.body, head;
        if (it.base < 0) {
            e.packed_type =
                int(std::find(std::begin(type_names),
                              std::end(type_names), it.type) -
                    std::begin(type_names));
            head = entry_head(e.packed_type, raw.size());
        } else {
            auto& b = ents[size_t(it.base)];
            raw = make_delta(b.body, it.body);
            e.delta = raw, e.packed_type = ofs_delta, e.base = b.oid;
            e.depth = b.depth + 1, e.base_offset = long(b.offset);
            head = entry_head(ofs_delta, raw.size()) +
                   ofs_out(e.offset - b.offset);
        }
        out += head + compress(raw);
        e.end = out.size();
        e.crc = crc32(std::string_view(out).substr(e.offset));
        ents.push_back(std::move(e));
    }
    return {out + sha1_raw(out), ents};
}

// verify_lines 는 git verify-pack -v 와 바이트까지 같은 줄들(§13.3).
std::vector<std::string> verify_lines(std::vector<PackEntry> ents,
                                      const std::string& pack_path) {
    std::sort(ents.begin(), ents.end(),
              [](auto& a, auto& b) { return a.offset < b.offset; });
    std::vector<std::string> rows;
    std::map<int, int> hist;
    for (size_t k = 0; k < ents.size(); ++k) {
        auto& e = ents[k];
        size_t end = k + 1 < ents.size() ? ents[k + 1].offset : e.end;
        // 크기는 팩에 적힌 크기 — 델타면 델타의 크기다(git 과 같다)
        size_t size = e.delta ? e.delta->size() : e.body.size();
        char buf[160];
        std::snprintf(buf, sizeof buf, "%s %-6s %zu %zu %zu",
                      e.oid.c_str(), e.type.c_str(), size,
                      end - e.offset, e.offset);
        rows.push_back(buf);
        if (e.depth)
            rows.back() += " " + std::to_string(e.depth) + " " + e.base;
        hist[e.depth]++;
    }
    auto plural = [](int n) {
        return std::to_string(n) + (n == 1 ? " object" : " objects");
    };
    rows.push_back("non delta: " + plural(hist[0]));
    for (auto& [d, n] : hist)
        if (d)
            rows.push_back("chain length = " + std::to_string(d) +
                           ": " + plural(n));
    rows.push_back(pack_path + ": ok");
    return rows;
}

// packed_objects 는 objects/pack 의 팩 안 객체 전부(SPEC.md §5.2).
// 작은 저장소를 위한 곧은 방법이다 — 색인으로 자리를 찾아 그 항목만
// 푸는 대신 팩 전체를 되살려 (경로·크기·시각)마다 기억해 둔다.
std::map<std::string, Object> packed_objects(
    const std::string& gitdir) {
    namespace fs = std::filesystem;
    static std::map<std::string, std::map<std::string, Object>> cache;
    std::map<std::string, Object> out;
    std::error_code ec;
    std::vector<std::string> idx;
    for (auto& f : fs::directory_iterator(gitdir + "/objects/pack", ec))
        if (f.path().extension() == ".idx") idx.push_back(f.path());
    std::sort(idx.begin(), idx.end());
    for (auto& ip : idx) {
        auto pp = ip.substr(0, ip.size() - 4) + ".pack";
        struct stat st;
        if (::stat(pp.c_str(), &st) != 0) continue;  // 짝 .pack 이 없다
        auto key = pp + "\n" + std::to_string(st.st_size) + "\n" +
                   std::to_string(st.st_mtim.tv_sec) + "." +
                   std::to_string(st.st_mtim.tv_nsec);
        if (!cache.count(key)) {
            auto& objs = cache[key];
            auto ents = read_pack(try_read(pp).value(), [&](auto& o) {
                return read_object(gitdir, o);
            });
            for (auto& e : ents) objs[e.oid] = {e.type, e.body};
        }
        for (auto& [o, v] : cache[key]) out.emplace(o, v);
    }
    return out;
}
}  // namespace mygit
