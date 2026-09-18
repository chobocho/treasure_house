package mygit.tests;

import static java.nio.charset.StandardCharsets.ISO_8859_1;
import static mygit.tests.Check.eq;
import static mygit.tests.Check.gitError;
import static mygit.tests.Check.ok;

import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.attribute.PosixFilePermissions;
import java.util.Arrays;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import mygit.Fs;
import mygit.Objects;
import mygit.Zlib;

// zlib 겉옷과 느슨한 객체의 시험 — SPEC.md §3 · §4.1 · §4.6, 2단계.
//
// golden/objects/ 는 진짜 git 이 쓴 파일 그대로이고(고정·동적 허프만
// 블록이 섞여 있다), golden/stored/ 는 C++ 이 쓸 저장 블록 꼴인데 진짜
// git 이 읽고 fsck --strict 를 통과한 것이다(golden/stored_ok.txt).
final class ObjectsTest {
  static final String HELLO =
      "ce013625030ba8dba906f756967f9e9ca394464a";

  private ObjectsTest() {}

  static List<Map<String, String>> objs() throws Exception {
    return Golden.tsv("objects", "objects.tsv");
  }

  // 풀린 객체 바이트 → [형식, 크기, 몸]
  static Object[] split(byte[] raw) {
    int nul = 0;
    while (raw[nul] != 0) nul++;
    String[] head = new String(raw, 0, nul, ISO_8859_1).split(" ");
    byte[] body = Arrays.copyOfRange(raw, nul + 1, raw.length);
    return new Object[] {head[0], Integer.parseInt(head[1]), body};
  }

  static void s3_2_inflatesEveryGitWrittenObject() throws Exception {
    Set<String> btypes = new HashSet<>();
    for (var row : objs()) {
      Object[] t = split(Zlib.decompress(
          Golden.read("objects", row.get("id"))));
      eq(row.get("type"), t[0]);
      eq(Integer.parseInt(row.get("size")), t[1]);
      eq(t[1], ((byte[]) t[2]).length);
      btypes.add(row.get("btype"));
    }
    // 고정(1)과 동적(2) 허프만이 둘 다 있어야 이 시험이 뜻이 있다
    eq(Set.of("1", "2"), btypes);
  }

  static void s3_2_inflatesStoredBlocks() throws Exception {
    for (String name : Fs.list(Golden.path("stored"))) {
      Object[] t = split(Zlib.decompress(Golden.read("stored", name)));
      eq(t[1], ((byte[]) t[2]).length, name);
    }
  }

  static void s3_1_roundTrip() throws Exception {
    for (byte[] data : new byte[][] {{}, {'x'},
        Golden.make("counter:70000")}) {
      eq(data, Zlib.decompress(Zlib.compress(data)));
    }
  }

  static void s3_2_prefixReportsConsumedBytes() throws Exception {
    // 팩 안에서는 스트림이 끝나는 곳을 알아야 다음 항목을 읽는다
    byte[] a = Zlib.compress("first stream".getBytes());
    byte[] b = Zlib.compress("second".getBytes());
    byte[] data = new byte[4 + a.length + b.length];
    System.arraycopy(a, 0, data, 4, a.length);
    System.arraycopy(b, 0, data, 4 + a.length, b.length);
    var x = Zlib.decompressPrefix(data, 4);
    eq("first stream", new String(x.data(), ISO_8859_1));
    eq(a.length, x.used());
    var y = Zlib.decompressPrefix(data, 4 + x.used());
    eq("second", new String(y.data(), ISO_8859_1));
    eq(b.length, y.used());
  }

  static void s3_2_badAdlerIsAnError() throws Exception {
    byte[] raw = Golden.read("objects", HELLO);
    raw[raw.length - 1] ^= (byte) 0xff;
    gitError(() -> Zlib.decompress(raw));
  }

  static void s3_adler32() {
    eq(0x11e60398L, Zlib.adler32("Wikipedia".getBytes()));
    eq(1L, Zlib.adler32(new byte[0]));
  }

  static void s4_1_knownNames() {
    eq(HELLO, Objects.hashObject("blob", "hello\n".getBytes()));
    eq("e69de29bb2d1d6434b8b29ae775ad8c2e48c5391",
        Objects.hashObject("blob", new byte[0]));
    eq("4b825dc642cb6eb9a060e54bf8d69288fbee4904",
        Objects.hashObject("tree", new byte[0]));
  }

  static void s4_1_everyGoldenObjectHashesToItsName() throws Exception {
    for (var row : objs()) {
      Object[] t = split(Zlib.decompress(
          Golden.read("objects", row.get("id"))));
      eq(row.get("id"), Objects.hashObject((String) t[0],
          (byte[]) t[2]));
    }
  }

  // 임시 .git 하나로 body 를 돌리고 지운다
  interface InRepo { void run(String gitdir) throws Exception; }

  static void withRepo(InRepo body) throws Exception {
    String tmp = Golden.tempdir();
    try {
      String g = Fs.join(tmp, ".git");
      Fs.mkdirs(Fs.join(g, "objects", "pack"));
      body.run(g);
    } finally {
      Golden.rmTree(tmp);
    }
  }

  static void plant(String gitdir, String oid) throws Exception {
    String p = Objects.objectPath(gitdir, oid);
    Fs.mkdirs(Path.of(p).getParent().toString());
    Fs.write(p, Golden.read("objects", oid));
  }

  // 이 파일 시스템이 0444 를 지키는가.
  //
  // 이 덱을 만든 기계(안드로이드 위 proot)의 저장소 디렉터리는 쓰기
  // 비트를 지우지 못한다 — 진짜 git 이 쓴 객체도 여기서는 0644 로
  // 보인다(2026-09-18 확인). 권한을 못 지키는 곳에서 0444 를 단언하면
  // 구현이 아니라 기계를 시험하게 된다.
  static boolean honoursReadonly(String where) throws Exception {
    Path probe = Path.of(where, "probe");
    Files.write(probe, new byte[0]);
    Files.setPosixFilePermissions(probe,
        PosixFilePermissions.fromString("r--r--r--"));
    Path moved = Files.move(probe, Path.of(where, "probe2"));
    boolean ok = PosixFilePermissions.toString(
        Files.getPosixFilePermissions(moved)).equals("r--r--r--");
    Files.delete(moved);
    return ok;
  }

  static void s4_6_pathAndContent() throws Exception {
    withRepo(g -> {
      eq(HELLO, Objects.writeObject(g, "blob", "hello\n".getBytes()));
      String p = Objects.objectPath(g, HELLO);
      byte[] raw = Zlib.decompress(Fs.read(p));
      eq("blob 6\0hello\n", new String(raw, ISO_8859_1));
    });
  }

  static void s4_6_readonly() throws Exception {
    withRepo(g -> {
      if (!honoursReadonly(g)) {
        Check.skip("이 파일 시스템은 0444 를 지키지 않는다");
      }
      Objects.writeObject(g, "blob", "hello\n".getBytes());
      eq("r--r--r--", PosixFilePermissions.toString(
          Files.getPosixFilePermissions(
              Path.of(Objects.objectPath(g, HELLO)))));
    });
  }

  static void s4_6_secondWriteIsANoOp() throws Exception {
    withRepo(g -> {
      Objects.writeObject(g, "blob", "hello\n".getBytes());
      // 파일이 0444 여도 두 번째 쓰기가 실패하면 안 된다
      Objects.writeObject(g, "blob", "hello\n".getBytes());
      eq(List.of(HELLO.substring(2)),
          Fs.list(Fs.join(g, "objects", "ce")));
    });
  }

  static void s4_6_noTempFilesLeft() throws Exception {
    withRepo(g -> {
      Objects.writeObject(g, "blob", new byte[1000]);
      try (var s = Files.walk(Path.of(g))) {
        for (Path p : s.filter(Files::isRegularFile).toList()) {
          eq(40, p.getParent().getFileName().toString().length()
              + p.getFileName().toString().length(), p);
        }
      }
    });
  }

  static void s4_6_readsWhatGitWrote() throws Exception {
    withRepo(g -> {
      for (var row : objs()) {
        plant(g, row.get("id"));
        var o = Objects.readObject(g, row.get("id"));
        eq(row.get("type"), o.type());
        eq(Integer.parseInt(row.get("size")), o.body().length);
      }
    });
  }

  static void s4_6_readsWhatItWrote() throws Exception {
    withRepo(g -> {
      String oid = Objects.writeObject(g, "commit", "x\n".getBytes());
      var o = Objects.readObject(g, oid);
      eq("commit", o.type());
      eq("x\n".getBytes(), o.body());
    });
  }

  static void s4_6_missingObject() throws Exception {
    withRepo(g -> gitError(() -> Objects.readObject(g, HELLO)));
  }

  static void s4_6_sizeMismatchIsAnError() throws Exception {
    withRepo(g -> {
      Fs.mkdirs(Fs.join(g, "objects", "ce"));
      Fs.write(Objects.objectPath(g, HELLO),
          Zlib.compress("blob 7\0hello\n".getBytes()));
      gitError(() -> Objects.readObject(g, HELLO));
    });
  }

  static void s4_6_prefix() throws Exception {
    withRepo(g -> {
      for (var row : objs()) plant(g, row.get("id"));
      for (var row : objs()) {
        String oid = row.get("id");
        eq(oid, Objects.findObject(g, oid.substring(0, 7)));
        eq(oid, Objects.findObject(g, oid));
      }
      eq(null, Objects.findObject(g, "ffffff"));
    });
  }

  static void s4_6_ambiguousPrefix() throws Exception {
    // 앞 네 글자가 같아질 때까지 blob 을 만들어 본다 — 65,536 칸에
    // 생일 문제라 수백 번이면 짝이 나온다
    withRepo(g -> {
      Map<String, byte[]> seen = new HashMap<>();
      for (int k = 0;; k++) {
        byte[] body = (k + "\n").getBytes();
        String p = Objects.hashObject("blob", body).substring(0, 4);
        if (seen.containsKey(p)) {
          Objects.writeObject(g, "blob", seen.get(p));
          Objects.writeObject(g, "blob", body);
          gitError(() -> Objects.findObject(g, p));
          return;
        }
        seen.put(p, body);
      }
    });
  }

  static void s4_6_shortPrefixIsRefused() throws Exception {
    withRepo(g -> {
      plant(g, HELLO);
      ok(Objects.findObject(g, "ce0") == null, "ce0");
    });
  }
}
