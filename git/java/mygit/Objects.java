package mygit;

import static java.nio.charset.StandardCharsets.ISO_8859_1;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.nio.file.attribute.PosixFilePermissions;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.TreeSet;

// 객체 (SPEC.md §4.1 · §4.6) — 이름은 내용의 SHA-1 이다.
//
// 이름 = SHA-1("<형식> <크기>\0" + 몸). 같은 내용은 어느 저장소에서
// 누가 만들어도 같은 이름을 얻는다 — git 이 "내용 주소 저장소" 인
// 까닭이 이 한 줄이다. 느슨한 객체는 그 바이트를 zlib 으로 눌러
// .git/objects/<앞 2글자>/<나머지 38글자> 에 둔다.
//
// 느슨한 객체에 없으면 팩(objects/pack/*.pack)에서 찾는다(SPEC.md
// §5.2). 이름이 java.util.Objects 와 같지만 SPEC §15 의 모듈 이름을
// 따랐다 — 이 패키지 안에서는 이쪽이 이긴다.
public final class Objects {
  public static final List<String> TYPES =
      List.of("blob", "tree", "commit", "tag");

  private Objects() {}

  // 객체 하나 — 형식과 몸
  public record Obj(String type, byte[] body) {}

  private static byte[] header(String type, byte[] body) {
    return (type + " " + body.length + "\0").getBytes(ISO_8859_1);
  }

  // 객체 이름(16진 40글자). 저장소를 건드리지 않는다. 머리와 몸을
  // 이어 붙이지 않고 차례로 흘려 넣는다 — 큰 blob 을 복사하지 않는다.
  public static String hashObject(String type, byte[] body) {
    return java.util.HexFormat.of().formatHex(new Sha1()
        .update(header(type, body)).update(body).digest());
  }

  public static String objectPath(String gitdir, String oid) {
    return Fs.join(gitdir, "objects", oid.substring(0, 2),
        oid.substring(2));
  }

  // 느슨한 객체 하나를 쓰고 이름을 돌려준다.
  //
  // 이미 있으면 아무것도 하지 않는다 — 이름이 같으면 내용도 같기
  // 때문이다(0444 라 덮어쓰려 하면 실패하기도 한다). 임시 파일에 다
  // 쓴 뒤 이름을 바꿔 넣어, 도중에 죽어도 반쯤 쓴 객체가 남지 않는다.
  public static String writeObject(String gitdir, String type,
      byte[] body) {
    String oid = hashObject(type, body);
    Path file = Path.of(objectPath(gitdir, oid));
    if (Files.exists(file)) return oid;
    Path tmp = null;
    try {
      Files.createDirectories(file.getParent());
      tmp = Files.createTempFile(file.getParent(), "tmp_obj_", "");
      byte[] head = header(type, body);
      byte[] raw = Arrays.copyOf(head, head.length + body.length);
      System.arraycopy(body, 0, raw, head.length, body.length);
      Files.write(tmp, Zlib.compress(raw));
      Files.setPosixFilePermissions(tmp,
          PosixFilePermissions.fromString("r--r--r--"));
      Files.move(tmp, file, StandardCopyOption.ATOMIC_MOVE);
    } catch (IOException e) {
      try {
        if (tmp != null) Files.deleteIfExists(tmp);
      } catch (IOException ignored) {
        // 지우지 못한 임시 파일보다 처음 오류가 중요하다
      }
      throw new UncheckedIOException(e);
    }
    return oid;
  }

  // 풀린 바이트 → 객체. 머리의 크기가 몸과 다르면 오류.
  static Obj parseRaw(byte[] raw, String oid) {
    int nul = 0;
    while (nul < raw.length && raw[nul] != 0) nul++;
    String[] parts = new String(raw, 0, nul, ISO_8859_1).split(" ");
    if (nul == raw.length || parts.length != 2
        || !parts[1].matches("\\d+")) {
      throw new GitError("fatal: mygit: bad object header in " + oid);
    }
    byte[] body = Arrays.copyOfRange(raw, nul + 1, raw.length);
    if (!TYPES.contains(parts[0])
        || !parts[1].equals(String.valueOf(body.length))) {
      throw new GitError("fatal: mygit: object " + oid + " is corrupt");
    }
    return new Obj(parts[0], body);
  }

  private static final Map<String, Map<String, Obj>> PACKS =
      new HashMap<>();

  // 팩 안 객체 전부 {이름: 객체}. 팩마다 한 번만 읽는다.
  //
  // 작은 저장소를 위한 곧은 방법이다 — 색인으로 자리를 찾아 그 항목만
  // 푸는 대신 팩 전체를 되살려 기억해 둔다(11단계, SPEC.md §5.2).
  // 기억의 열쇠에 크기·수정 시각을 넣어, 같은 이름의 팩이 바뀌면 다시
  // 읽는다. 찾는 차례는 파일 이름 차례이고 먼저 찾은 것이 이긴다.
  static Map<String, Obj> packedObjects(String gitdir) {
    Map<String, Obj> out = new HashMap<>();
    String dir = Fs.join(gitdir, "objects", "pack");
    for (String f : Fs.list(dir)) {
      String pack = Fs.join(dir, f.replaceAll("\\.idx$", ".pack"));
      if (!f.endsWith(".idx") || !Fs.exists(pack)) continue;
      String key;
      try {
        Path p = Path.of(pack);
        key = pack + "\0" + Files.size(p) + "\0"
            + Files.getLastModifiedTime(p).toMillis();
      } catch (IOException e) {
        throw new UncheckedIOException(e);
      }
      Map<String, Obj> objs = PACKS.get(key);
      if (objs == null) {
        objs = new HashMap<>();
        for (Pack.PackEntry e : Pack.readPack(Fs.read(pack),
            o -> readObject(gitdir, o))) {
          objs.put(e.oid, new Obj(e.type, e.body));
        }
        PACKS.put(key, objs);
      }
      objs.forEach(out::putIfAbsent);
    }
    return out;
  }

  // 느슨한 객체를 먼저, 없으면 팩. 없으면 GitError.
  public static Obj readObject(String gitdir, String oid) {
    byte[] raw = Fs.readOrNull(objectPath(gitdir, oid));
    if (raw != null) return parseRaw(Zlib.decompress(raw), oid);
    Obj hit = packedObjects(gitdir).get(oid);
    if (hit == null) {
      throw new GitError("fatal: mygit: object " + oid + " not found");
    }
    return hit;
  }

  // 느슨한 객체의 이름 전부. objects/xx/ 디렉터리를 훑는다.
  public static List<String> allLoose(String gitdir) {
    String root = Fs.join(gitdir, "objects");
    List<String> out = new ArrayList<>();
    for (String d : Fs.list(root)) {
      if (d.length() != 2) continue;
      for (String f : Fs.list(Fs.join(root, d))) {
        if (f.length() == 38) out.add(d + f);
      }
    }
    return out;
  }

  // 앞부분(4글자 이상)으로 찾는다: 하나면 그 이름, 없으면 null.
  //
  // 둘 이상이면 git 처럼 모호하다고 멈춘다. 4글자보다 짧으면 찾지
  // 않는다(git 의 최소 줄임 길이와 같다). O(느슨한 객체 수).
  public static String findObject(String gitdir, String prefix) {
    String p = prefix.toLowerCase();
    if (p.length() < 4 || !p.matches("[0-9a-f]+")) return null;
    TreeSet<String> ids = new TreeSet<>(allLoose(gitdir));
    ids.addAll(packedObjects(gitdir).keySet());
    if (p.length() == 40) return ids.contains(p) ? p : null;
    List<String> hits = ids.stream().filter(o -> o.startsWith(p))
        .toList();
    if (hits.size() > 1) {
      throw new GitError("error: short object ID " + prefix
          + " is ambiguous");
    }
    return hits.isEmpty() ? null : hits.get(0);
  }
}
