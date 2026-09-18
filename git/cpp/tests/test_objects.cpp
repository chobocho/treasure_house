// zlib 겉옷과 느슨한 객체의 시험 — SPEC.md §3 · §4.1 · §4.6, 2단계.
// golden/objects 는 git 이 쓴 파일(고정·동적 허프만 블록)이다 — 손으로
// 짠 inflate 가 전부 풀어야 한다. golden/stored 는 이 구현이 쓸 저장
// 블록 꼴을 git 이 fsck --strict 로 받아들인 것이고, compress 는 그
// 바이트를 그대로 내야 한다.
#include <set>

#include "golden.hpp"

using namespace mygit;

namespace {
const std::string hello = "ce013625030ba8dba906f756967f9e9ca394464a";

std::string body_of(const std::string& raw) {
    return raw.substr(raw.find('\0') + 1);
}
}  // namespace

TEST(s3_inflate_git_objects) {
    std::set<std::string> btypes;
    for (auto& r : golden::tsv("objects/objects.tsv")) {
        auto raw = decompress(golden::read("objects/" + r["id"]));
        auto sp = raw.find(' '), nul = raw.find('\0');
        CHECK_EQ(raw.substr(0, sp), r["type"]);
        CHECK_EQ(raw.substr(sp + 1, nul - sp - 1), r["size"]);
        CHECK_EQ(hash_object(r["type"], body_of(raw)), r["id"]);
        btypes.insert(r["btype"]);
    }
    CHECK(btypes.count("1") && btypes.count("2"));
}

TEST(s3_1_stored_blocks_are_byte_identical) {
    int n = 0;
    for (auto& e : golden::fs::directory_iterator("golden/stored")) {
        auto want = golden::read_file(e.path());
        auto raw = decompress(want);
        CHECK_EQ(compress(raw), want);
        CHECK_EQ(sha1_hex(raw), e.path().filename().string());
        ++n;
    }
    CHECK_EQ(n, 4);
}

TEST(s3_round_trip_and_prefix) {
    for (auto d : {std::string(), std::string("x"),
                   golden::make("counter:70000"),
                   golden::make("counter:131071")})
        CHECK(decompress(compress(d)) == d);
    auto a = golden::read("objects/" + hello);  // git 의 스트림
    auto b = compress("second");
    auto data = "JUNK" + a + b;
    auto [out, used] = decompress_prefix(data, 4);
    CHECK_EQ(out, std::string("blob 6\0hello\n", 13));
    CHECK_EQ(used, a.size());
    auto [out2, used2] = decompress_prefix(data, 4 + used);
    CHECK_EQ(out2, "second");
    CHECK_EQ(used2, b.size());
    auto bad = a;
    bad.back() ^= 0xff;
    CHECK_EQ(golden::git_error([&] { decompress(bad); }).what(),
             std::string("fatal: mygit: corrupt zlib stream"));
    golden::git_error([&] { decompress(a.substr(0, a.size() - 3)); });
    golden::git_error([&] { decompress(a + "x"); });
    CHECK_EQ(adler32("Wikipedia"), 0x11e60398u);
    CHECK_EQ(adler32(""), 1u);
    CHECK_EQ(crc32("123456789"), 0xcbf43926u);
}

TEST(s4_6_write_read_find) {
    CHECK_EQ(hash_object("tree", ""),
             "4b825dc642cb6eb9a060e54bf8d69288fbee4904");
    golden::TempDir t;
    auto g = golden::gitdir(t);
    CHECK_EQ(write_object(g, "blob", "hello\n"), hello);
    CHECK_EQ(write_object(g, "blob", "hello\n"), hello);  // 두 번째
    CHECK_EQ(decompress(golden::read_file(object_path(g, hello))),
             std::string("blob 6\0hello\n", 13));
    for (auto& r : golden::tsv("objects/objects.tsv")) {
        golden::plant(g, r["id"]);
        auto o = read_object(g, r["id"]);
        CHECK_EQ(o.type, r["type"]);
        CHECK_EQ(std::to_string(o.body.size()), r["size"]);
        CHECK_EQ(find_object(g, r["id"].substr(0, 7)), r["id"]);
    }
    CHECK_EQ(find_object(g, "ffffff"), "");
    golden::git_error([&] { read_object(g, std::string(40, '1')); });
}

TEST(s4_6_size_mismatch_and_ambiguous) {
    golden::TempDir t;
    auto g = golden::gitdir(t);
    golden::write_file(object_path(g, hello),
                       compress(std::string("blob 7\0hello\n", 13)));
    golden::git_error([&] { read_object(g, hello); });
    std::map<std::string, std::string> seen;
    for (int k = 0;; ++k) {
        auto body = std::to_string(k) + "\n";
        auto oid = hash_object("blob", body);
        if (seen.count(oid.substr(0, 4))) {
            write_object(g, "blob", seen[oid.substr(0, 4)]);
            write_object(g, "blob", body);
            golden::git_error(
                [&] { find_object(g, oid.substr(0, 4)); });
            return;
        }
        seen[oid.substr(0, 4)] = body;
    }
}
