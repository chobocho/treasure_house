package mygit.tests;

import static java.nio.charset.StandardCharsets.UTF_8;
import static mygit.tests.Check.eq;
import static mygit.tests.Check.ok;

import java.util.Arrays;
import java.util.HashMap;
import java.util.Map;
import mygit.Cli;
import mygit.Zlib;

// blob — hash-object · cat-file 의 시험. SPEC.md §1 · §9, 3단계.
//
// 오라클은 golden/objects/ 의 blob 들(진짜 git 이 쓴 파일)과
// golden/errors.tsv 의 오류 문장이다. 명령은 Cli.run 으로 과정 안에서
// 부른다 — 새 JVM 을 띄우지 않아 빠르고, 출력 바이트를 그대로 본다.
final class BlobTest {
  private BlobTest() {}

  static byte[] bodyOf(String oid) throws Exception {
    byte[] raw = Zlib.decompress(Golden.read("objects", oid));
    int nul = 0;
    while (raw[nul] != 0) nul++;
    return Arrays.copyOfRange(raw, nul + 1, raw.length);
  }

  // errors.tsv — 명령 → "코드 첫 줄" (Sandbox.firstLine 의 꼴)
  static Map<String, String> errors() throws Exception {
    Map<String, String> out = new HashMap<>();
    for (var r : Golden.tsv("errors.tsv")) {
      out.put(r.get("command"),
          r.get("exit") + " " + r.get("stderr-first-line"));
    }
    return out;
  }

  static void s9_everyGoldenBlobHasItsGitName() throws Exception {
    int n = 0;
    try (var sb = new Sandbox(true)) {
      for (var row : ObjectsTest.objs()) {
        if (!row.get("type").equals("blob")) continue;
        sb.put("f", bodyOf(row.get("id")));
        Cli.Result r = sb.mygit("hash-object", "f");
        eq(0, r.code());
        eq(row.get("id") + "\n", new String(r.out(), UTF_8));
        eq(0, r.err().length);
        n++;
      }
    }
    ok(n >= 3, n);
  }

  static void s9_stdin() throws Exception {
    try (var sb = new Sandbox(true)) {
      byte[] out = sb.mygit("hello\n".getBytes(), "hash-object",
          "--stdin").out();
      eq(ObjectsTest.HELLO + "\n", new String(out, UTF_8));
    }
  }

  static void s9_typeOption() throws Exception {
    try (var sb = new Sandbox(true)) {
      eq("4b825dc642cb6eb9a060e54bf8d69288fbee4904\n",
          sb.out("hash-object", "-t", "tree", "--stdin"));
    }
  }

  static void s9_writeThenReadBack() throws Exception {
    try (var sb = new Sandbox(true)) {
      byte[] data = Golden.make("counter:5000");
      sb.put("f", data);
      String oid = sb.out("hash-object", "-w", "f").strip();
      eq("blob\n", sb.out("cat-file", "-t", oid));
      eq("5000\n", sb.out("cat-file", "-s", oid));
      Cli.Result r = sb.mygit("cat-file", "-p", oid);
      eq(0, r.code());
      eq(data, r.out());
      eq(0, r.err().length);
      // 앞부분 7글자로도 찾는다
      eq(data, sb.mygit("cat-file", "-p", oid.substring(0, 7)).out());
    }
  }

  static void s1_4_missingFile() throws Exception {
    try (var sb = new Sandbox(true)) {
      eq(errors().get("hash-object nope"),
          Sandbox.firstLine(sb.mygit("hash-object", "nope")));
    }
  }

  static void s9_commitAndTagPrintTheirBodies() throws Exception {
    try (var sb = new Sandbox(true)) {
      for (var row : ObjectsTest.objs()) {
        String oid = row.get("id");
        if (row.get("type").equals("tree")) continue;
        sb.plant(oid);
        Cli.Result r = sb.mygit("cat-file", "-p", oid);
        eq(0, r.code());
        eq(bodyOf(oid), r.out());
        eq(row.get("type") + "\n", sb.out("cat-file", "-t", oid));
      }
    }
  }

  static void s1_4_notAValidObjectName() throws Exception {
    try (var sb = new Sandbox(true)) {
      eq(errors().get("cat-file -p nope"),
          Sandbox.firstLine(sb.mygit("cat-file", "-p", "nope")));
    }
  }

  static void s1_4_notARepository() throws Exception {
    try (var sb = new Sandbox(false)) {
      eq(errors().get("status"),
          Sandbox.firstLine(sb.mygit("cat-file", "-t", "abcd")));
    }
  }

  static void s1_1_hashObjectNeedsNoRepo() throws Exception {
    try (var sb = new Sandbox(false)) {
      sb.put("f", "hello\n".getBytes());
      eq(0, sb.mygit("hash-object", "f").code());
    }
  }

  static void s1_4_unknownCommand() throws Exception {
    try (var sb = new Sandbox(false)) {
      Cli.Result r = sb.mygit("frobnicate");
      eq(1, r.code());
      eq("mygit: 'frobnicate' is not a mygit command.\n",
          new String(r.err(), UTF_8));
    }
  }
}
