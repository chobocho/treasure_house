package mygit.tests;

import static java.nio.charset.StandardCharsets.ISO_8859_1;
import static java.nio.charset.StandardCharsets.UTF_8;
import static mygit.tests.Check.eq;
import static mygit.tests.Check.gitError;
import static mygit.tests.Check.ok;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.HexFormat;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.TreeSet;
import mygit.Cli;
import mygit.Fs;
import mygit.Objects;
import mygit.Pack;
import mygit.Pack.PackEntry;

// 팩의 시험 — SPEC.md §13, 11단계 "packfile — 읽기, 그다음 쓰기".
//
// golden/pack/ 은 진짜 git 이 쓴 팩 둘이다 — ofs(repack 이 쓴,
// OFS_DELTA)와 ref(pack-objects 가 쓴, REF_DELTA). .verify 는 git
// verify-pack -v, .show-index 는 git show-index 의 출력이다. 가장 강한
// 시험은 git 의 팩에서 mygit 이 다시 만든 색인이 git 의 .idx 와
// 바이트까지 같은가다.
final class PackTest {
  static final List<String> NAMES = List.of("ofs", "ref");

  private PackTest() {}

  // git show-index → "자리 이름 crc8글자" 줄들
  static List<String> showIndex(String name) throws Exception {
    List<String> rows = new ArrayList<>();
    for (String line : new String(Golden.read("pack",
        name + ".show-index"), UTF_8).split("\n")) {
      if (!line.isEmpty()) rows.add(line.replaceAll("[()]", ""));
    }
    return rows;
  }

  static List<PackEntry> read(String name) throws Exception {
    return Pack.readPack(Golden.read("pack", name + ".pack"), null);
  }

  static int size(PackEntry e) {
    return (e.delta != null ? e.delta : e.body).length;
  }

  static void s13_1_everyObjectAndItsDeltaChain() throws Exception {
    for (String name : NAMES) {
      Map<String, String[]> want = new HashMap<>();
      for (String line : new String(Golden.read("pack",
          name + ".verify"), UTF_8).split("\n")) {
        String[] cols = line.split("\\s+");
        if (cols.length >= 5 && cols[0].length() == 40) {
          want.put(cols[0], cols);
        }
      }
      var ents = read(name);
      eq(want.keySet(), Set.copyOf(ents.stream().map(e -> e.oid)
          .toList()), name);
      for (PackEntry e : ents) {
        String[] cols = want.get(e.oid);
        // 크기 칸은 팩에 적힌 크기 — 델타면 델타의 크기(§13.3)
        eq(cols[1] + " " + cols[2] + " " + cols[4],
            e.type + " " + size(e) + " " + e.offset, e.oid);
        if (cols.length > 5) {
          eq(cols[5] + " " + cols[6], e.depth + " " + e.base, e.oid);
        }
        eq(e.oid, Objects.hashObject(e.type, e.body));
      }
      int kind = name.equals("ofs") ? 6 : 7;
      ok(ents.stream().anyMatch(e -> e.packedType == kind), name);
    }
  }

  static void s13_2_idxMatchesShowIndex() throws Exception {
    for (String name : NAMES) {
      var idx = Pack.readIdx(Golden.read("pack", name + ".idx"));
      eq(new TreeSet<>(showIndex(name)), new TreeSet<>(idx.entries()
          .stream().map(x -> x.offset() + " " + x.oid() + " "
              + String.format("%08x", x.crc())).toList()), name);
    }
  }

  static void s13_1_badTrailer() throws Exception {
    byte[] data = Golden.read("pack", "ofs.pack");
    data[data.length - 1] ^= 1;
    gitError(() -> Pack.readPack(data, null));
  }

  static void s13_2_rebuiltIdxIsByteIdenticalToGit() throws Exception {
    for (String name : NAMES) {
      byte[] data = Golden.read("pack", name + ".pack");
      eq(Golden.read("pack", name + ".idx"), Pack.writeIdx(
          Pack.readPack(data, null),
          Arrays.copyOfRange(data, data.length - 20, data.length)),
          name);
    }
  }

  static void s13_1_applyDeltasFromGit() throws Exception {
    int n = 0;
    for (String name : NAMES) {
      var ents = read(name);
      Map<String, PackEntry> byOid = new HashMap<>();
      ents.forEach(e -> byOid.put(e.oid, e));
      for (PackEntry e : ents) {
        if (e.base == null) continue;
        eq(e.body, Pack.applyDelta(byOid.get(e.base).body, e.delta));
        n++;
      }
    }
    ok(n > 0, n);
  }

  static void s13_3_makeDeltaBytesArePinned() {
    // SPEC.md §13.3 의 알고리즘을 손으로 따라가 얻은 바이트:
    // 크기 32 · 34, 복사(0,16), 끼움 "XY", 복사(0,16)
    String base = "0123456789abcdef".repeat(2);
    String target = base.substring(0, 16) + "XY" + base.substring(16);
    eq(HexFormat.of().parseHex("2022901002585990" + "10"),
        Pack.makeDelta(base.getBytes(), target.getBytes()));
  }

  static void s13_3_roundTrip() throws Exception {
    byte[] base = Golden.make("counter:70000");
    String b = new String(base, ISO_8859_1);
    String rev = new StringBuilder(b).reverse().toString();
    for (String t : List.of(b, b.substring(0, 30000) + "!"
        + b.substring(30000), "", "x".repeat(300),
        rev.substring(0, 5000) + b)) {
      byte[] target = t.getBytes(ISO_8859_1);
      eq(target, Pack.applyDelta(base, Pack.makeDelta(base, target)));
    }
  }

  static void s13_1_deltaErrors() throws Exception {
    // 예약 명령 0, 그리고 바탕 크기가 틀림
    gitError(() -> Pack.applyDelta("abc".getBytes(),
        new byte[] {3, 1, 0}));
    gitError(() -> Pack.applyDelta("abc".getBytes(),
        new byte[] {4, 1, 1, 'x'}));
  }

  static Sandbox repo() throws Exception {
    Sandbox sb = new Sandbox(false);
    CheckoutTest.ok(sb, "init");
    return sb;
  }

  static void s13_3_outputIsGitVerbatim() throws Exception {
    try (var sb = repo()) {
      for (String name : NAMES) {
        for (String ext : List.of(".pack", ".idx")) {
          sb.put(name + ext, Golden.read("pack", name + ext));
        }
        Cli.Result r = sb.mygit("verify-pack", "-v", name + ".idx");
        eq(0, r.code(), new String(r.err(), UTF_8));
        eq(Golden.read("pack", name + ".verify"), r.out(), name);
      }
    }
  }

  static void s13_3_unpackThenReadLoose() throws Exception {
    try (var sb = repo()) {
      sb.put("ofs.pack", Golden.read("pack", "ofs.pack"));
      CheckoutTest.ok(sb, "unpack-pack", "ofs.pack");
      for (String row : showIndex("ofs")) {
        String oid = row.split(" ")[1];
        ok(Fs.exists(Objects.objectPath(sb.gitdir, oid)), oid);
      }
    }
  }

  static void s5_2_readObjectFindsPackedObjects() throws Exception {
    try (var sb = repo()) {
      for (String ext : List.of(".pack", ".idx")) {
        Fs.write(Fs.join(sb.gitdir, "objects", "pack", "pack-x" + ext),
            Golden.read("pack", "ofs" + ext));
      }
      for (String row : showIndex("ofs")) {
        String oid = row.split(" ")[1];
        var o = Objects.readObject(sb.gitdir, oid);
        eq(oid, Objects.hashObject(o.type(), o.body()));
        eq(oid, Objects.findObject(sb.gitdir, oid.substring(0, 8)));
      }
    }
  }

  static List<PackEntry> packHistory(boolean delta) throws Exception {
    try (var sb = repo()) {
      StringBuilder body = new StringBuilder();
      for (int i = 0; i < 200; i++) {
        body.append("line ").append(i).append(" of a growing file\n");
      }
      for (int v = 0; v < 4; v++) {
        sb.put("grow.txt", (body + ("extra " + v + "\n").repeat(v + 1))
            .getBytes());
        CheckoutTest.ok(sb, "add", ".");
        CheckoutTest.ok(sb, "commit", "-m", "v" + v);
      }
      List<String> args = new ArrayList<>(List.of("pack-objects"));
      if (delta) args.add("--delta");
      args.add(".git/objects/pack/pack");
      String sha = CheckoutTest.ok(sb, args.toArray(new String[0]))
          .strip();
      String stem = Fs.join(sb.gitdir, "objects", "pack",
          "pack-" + sha);
      byte[] data = Fs.read(stem + ".pack");
      eq(sha, HexFormat.of().formatHex(data, data.length - 20,
          data.length));
      var ents = Pack.readPack(data, null);
      var oids = new TreeSet<>(ents.stream().map(e -> e.oid).toList());
      eq(oids, new TreeSet<>(Pack.readIdx(Fs.read(stem + ".idx"))
          .entries().stream().map(x -> x.oid()).toList()));
      eq(oids, new TreeSet<>(Objects.allLoose(sb.gitdir)));
      return ents;
    }
  }

  static void s13_3_plainPackHoldsEveryObject() throws Exception {
    ok(packHistory(false).stream().allMatch(e -> e.packedType < 5),
        "델타 없음");
  }

  static void s13_3_deltaPackUsesOfsDeltas() throws Exception {
    // 옛 판 셋이 한 판씩 새것을 바탕으로 — 깊이 1·2·3
    eq(List.of(1, 2, 3), packHistory(true).stream()
        .filter(e -> e.packedType == 6).map(e -> e.depth).sorted()
        .toList());
  }
}
