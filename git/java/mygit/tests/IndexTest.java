package mygit.tests;

import static java.nio.charset.StandardCharsets.ISO_8859_1;
import static mygit.tests.Check.eq;
import static mygit.tests.Check.gitError;
import static mygit.tests.Check.ok;

import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.attribute.FileTime;
import java.nio.file.attribute.PosixFilePermissions;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import mygit.Fs;
import mygit.Index;
import mygit.Index.IndexEntry;

// 인덱스의 시험 — SPEC.md §7, 6단계 "인덱스 — 스테이징의 실체".
//
// golden/index/ 의 세 파일은 진짜 git 이 쓴 인덱스다: 확장 없음(git
// add 직후), TREE 확장(git commit 뒤), 판 3(skip-worktree 가 켜진
// 항목). plain.bin 은 plain.raw 의 stat 칸을 §7.3 으로 지운 것이다.
final class IndexTest {
  private IndexTest() {}

  // golden/index/ls-stage.txt → "모드 이름 단계 경로" 줄들
  static List<String> lsStage() throws Exception {
    List<String> out = new ArrayList<>();
    for (String line : new String(Golden.read("index", "ls-stage.txt"),
        ISO_8859_1).split("\n")) {
      if (line.isEmpty()) continue;
      String[] mp = line.split("\t", 2);
      String[] m = mp[0].split(" ");
      out.add(Integer.parseInt(m[0], 8) + " " + m[1] + " " + m[2] + " "
          + TreeTest.unquote(mp[1]));
    }
    return out;
  }

  static List<String> summary(List<IndexEntry> ents) {
    return ents.stream().map(e -> e.mode + " " + e.oid + " " + e.stage
        + " " + e.path).toList();
  }

  static List<IndexEntry> parse(String name) throws Exception {
    return Index.parseIndex(Golden.read("index", name));
  }

  static void s7_1_plain() throws Exception {
    eq(lsStage(), summary(parse("plain.raw")));
  }

  static void s7_5_treeExtensionIsSkipped() throws Exception {
    eq(lsStage(), summary(parse("tree-ext.raw")));
  }

  static void s7_1_version3() throws Exception {
    var ents = parse("v3.raw");
    eq(lsStage(), summary(ents));
    eq(List.of("run.sh"), ents.stream().filter(e -> e.skipWorktree)
        .map(e -> e.path).toList());
  }

  static void s7_5_badChecksum() throws Exception {
    byte[] raw = Golden.read("index", "plain.raw");
    raw[raw.length - 1] ^= 1;
    gitError(() -> Index.parseIndex(raw));
  }

  static void s7_2_roundTripIsByteIdentical() throws Exception {
    byte[] raw = Golden.read("index", "plain.raw");
    eq(raw, Index.serializeIndex(Index.parseIndex(raw)));
  }

  static void s7_3_normalizedEqualsGolden() throws Exception {
    var ents = parse("plain.raw");
    for (IndexEntry e : ents) {
      e.ctimeS = e.ctimeNs = e.mtimeS = e.mtimeNs = 0;
      e.dev = e.ino = e.uid = e.gid = 0;
    }
    eq(Golden.read("index", "plain.bin"), Index.serializeIndex(ents));
  }

  static void s7_2_version3IsWrittenAsVersion2() throws Exception {
    byte[] data = Index.serializeIndex(parse("v3.raw"));
    eq(new byte[] {0, 0, 0, 2}, Arrays.copyOfRange(data, 4, 8));
  }

  static void s7_2_longPathAndPadding() {
    for (int n : new int[] {1, 2, 7, 8, 9, 100, 4094, 4095, 4096,
        5000}) {
      IndexEntry e = new IndexEntry("d/" + "x".repeat(n),
          "1".repeat(40), 0100644, 0);
      byte[] data = Index.serializeIndex(List.of(e));
      // 항목 길이는 8의 배수, NUL 은 1‥8 개
      int body = data.length - 12 - 20;
      eq(0, body % 8, n);
      int nuls = body - 62 - e.path.length();
      ok(1 <= nuls && nuls <= 8, n);
      eq(e.path, Index.parseIndex(data).get(0).path, n);
    }
  }

  static void s7_1_sortedByPathBytesThenStage() {
    List<IndexEntry> ents = new ArrayList<>();
    for (String ps : List.of("b 0", "a/x 0", "a-b 0", "c 3", "c 1",
        "c 2")) {
      String[] p = ps.split(" ");
      ents.add(new IndexEntry(p[0], "1".repeat(40), 0100644,
          Integer.parseInt(p[1])));
    }
    var back = Index.parseIndex(Index.serializeIndex(ents));
    eq(List.of("a-b 0", "a/x 0", "b 0", "c 1", "c 2", "c 3"),
        back.stream().map(e -> e.path + " " + e.stage).toList());
  }

  static void s7_2_execBitAndSize() throws Exception {
    String tmp = Golden.tempdir();
    try {
      Path p = Path.of(tmp, "run.sh");
      Files.write(p, "#!/bin/sh\n".getBytes());
      Files.setPosixFilePermissions(p,
          PosixFilePermissions.fromString("rwxr-xr-x"));
      IndexEntry e = Index.entryFromStat("run.sh", p.toString(),
          "2".repeat(40));
      eq(0100755, e.mode);
      eq(10, e.size);
      Files.setPosixFilePermissions(p,
          PosixFilePermissions.fromString("rw-r--r--"));
      e = Index.entryFromStat("run.sh", p.toString(), "2".repeat(40));
      eq(0100644, e.mode);
      FileTime mt = Files.getLastModifiedTime(p);
      eq(mt.toInstant().getEpochSecond(), (long) e.mtimeS);
      eq(mt.toInstant().getNano(), e.mtimeNs);
    } finally {
      Golden.rmTree(tmp);
    }
  }

  static void s7_4_writeAndReadBack() throws Exception {
    String tmp = Golden.tempdir();
    try {
      String g = Fs.join(tmp, ".git");
      Fs.mkdirs(g);
      eq(List.of(), Index.readIndex(g));
      Index.writeIndex(g, List.of(new IndexEntry("a", "3".repeat(40),
          0100644, 0)));
      eq(List.of("33188 " + "3".repeat(40) + " 0 a"),
          summary(Index.readIndex(g)));
      eq(false, Fs.exists(Fs.join(g, "index.lock")));
    } finally {
      Golden.rmTree(tmp);
    }
  }
}
