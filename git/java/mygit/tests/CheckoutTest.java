package mygit.tests;

import static java.nio.charset.StandardCharsets.UTF_8;
import static mygit.tests.Check.eq;

import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.attribute.PosixFilePermission;
import java.nio.file.attribute.PosixFilePermissions;
import mygit.Cli;
import mygit.Fs;

// 작업 트리 바꾸기의 시험 — SPEC.md §9.3, 9단계 "checkout · switch".
//
// 큰 오라클은 golden/scen/checkout.scn(진짜 git 의 switch·checkout
// 출력과 reflog)이다. 여기서는 장면이 직접 보지 않는 두 가지 — 파일이
// 없어져 비게 된 디렉터리가 지워지는가, 실행 비트가 작업 트리에
// 살아나는가 — 를 본다. git 도 둘 다 그렇게 한다(SPEC.md §9.3 끝).
final class CheckoutTest {
  private CheckoutTest() {}

  static Sandbox repo() throws Exception {
    Sandbox sb = new Sandbox(false);
    ok(sb, "init");
    return sb;
  }

  // 코드 0 을 단언하고 표준 출력을
  static String ok(Sandbox sb, String... args) {
    Cli.Result r = sb.mygit(args);
    eq(0, r.code(), String.join(" ", args),
        new String(r.err(), UTF_8));
    return new String(r.out(), UTF_8);
  }

  static void put(Sandbox sb, String rel, String data, String perm)
      throws Exception {
    Path p = Path.of(sb.root, rel);
    Files.createDirectories(p.getParent());
    Files.write(p, data.getBytes(UTF_8));
    Files.setPosixFilePermissions(p,
        PosixFilePermissions.fromString(perm));
  }

  static void s9_3_emptiedDirectoriesAreRemoved() throws Exception {
    try (var sb = repo()) {
      put(sb, "keep", "k\n", "rw-r--r--");
      ok(sb, "add", ".");
      ok(sb, "commit", "-m", "base");
      ok(sb, "switch", "-c", "deep");
      put(sb, "a/b/c.txt", "c\n", "rw-r--r--");
      ok(sb, "add", ".");
      ok(sb, "commit", "-m", "deep");
      ok(sb, "switch", "main");
      eq(false, Fs.exists(Fs.join(sb.root, "a")));
      ok(sb, "switch", "deep");
      eq("c\n", new String(Fs.read(Fs.join(sb.root, "a/b/c.txt")),
          UTF_8));
    }
  }

  static void s9_3_execBitIsWritten() throws Exception {
    try (var sb = repo()) {
      put(sb, "run", "#!/bin/sh\n", "rwxr-xr-x");
      ok(sb, "add", ".");
      ok(sb, "commit", "-m", "x");
      ok(sb, "switch", "-c", "side");
      Files.delete(Path.of(sb.root, "run"));
      ok(sb, "add", ".");
      ok(sb, "commit", "-m", "gone");
      ok(sb, "switch", "main");
      eq(true, Files.getPosixFilePermissions(Path.of(sb.root, "run"))
          .contains(PosixFilePermission.OWNER_EXECUTE));
    }
  }

  static void s9_3_statusIsCleanAfterSwitch() throws Exception {
    try (var sb = repo()) {
      put(sb, "f", "1\n", "rw-r--r--");
      ok(sb, "add", ".");
      ok(sb, "commit", "-m", "one");
      ok(sb, "switch", "-c", "b2");
      put(sb, "f", "2\n", "rw-r--r--");
      put(sb, "g/h", "h\n", "rw-r--r--");
      ok(sb, "add", ".");
      ok(sb, "commit", "-m", "two");
      for (String name : new String[] {"main", "b2", "main"}) {
        ok(sb, "switch", name);
        eq("", ok(sb, "status"), name);
      }
    }
  }
}
