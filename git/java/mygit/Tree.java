package mygit;

import static java.nio.charset.StandardCharsets.ISO_8859_1;

import java.io.ByteArrayOutputStream;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

// tree (SPEC.md §4.3) — 디렉터리 하나를 객체 하나로.
//
// 항목 = "<모드> <이름>\0<객체 이름 20바이트>". 이름과 권한은 blob 이
// 아니라 트리가 갖는다 — 같은 내용의 파일 둘은 blob 하나를 나눠 쓴다.
//
// **정렬 규칙이 전부다.** 항목은 이름의 바이트로 정렬하되 하위 트리는
// 이름 뒤에 '/' 가 붙은 것처럼 비교한다. 규칙을 한 글자만 어겨도
// 내용은 같고 이름이 다른 트리가 생기고, git 은 그것을 다른 역사로
// 본다.
//
// 이름·경로는 바이트 문자열(latin1)이다. Java 의 String.compareTo 는
// UTF-16 단위로 견주므로 한글이 섞이면 바이트 차례와 어긋나지만,
// 모든 글자가 0‥255 이면 compareTo 가 곧 바이트 비교다(SPEC.md §1.5).
public final class Tree {
  public static final String DIR = "40000";

  private Tree() {}

  // 트리 몸의 항목 하나와, 경로로 펼친 항목 하나
  public record Entry(String mode, String name, String oid) {}

  public record PathEntry(String mode, String oid, String path) {}

  // 정렬 열쇠. 하위 트리는 이름에 '/' 를 붙여 비교한다.
  public static String treeEntryKey(String mode, String name) {
    return mode.equals(DIR) ? name + "/" : name;
  }

  // 트리 몸 → 항목들. 적힌 차례 그대로.
  // O(몸의 길이). 몸이 중간에 끊기면 오류다.
  public static List<Entry> parseTree(byte[] body) {
    List<Entry> out = new ArrayList<>();
    String s = new String(body, ISO_8859_1);
    for (int i = 0; i < body.length;) {
      int sp = s.indexOf(' ', i);
      int nul = s.indexOf('\0', sp + 1);
      if (sp < 0 || nul < 0 || nul + 21 > body.length) {
        throw new GitError("fatal: mygit: corrupt tree object");
      }
      out.add(new Entry(s.substring(i, sp), s.substring(sp + 1, nul),
          HexFormat.of().formatHex(body, nul + 1, nul + 21)));
      i = nul + 21;
    }
    return out;
  }

  // 항목들 → 트리 몸. 정렬은 여기서 한다.
  //
  // 모드는 앞에 0 을 붙이지 않는다 — 디렉터리는 "40000" 다섯 글자다.
  // "040000" 은 cat-file -p 가 찍어 보일 때의 꼴일 뿐이다.
  public static byte[] serializeTree(List<Entry> entries) {
    ByteArrayOutputStream out = new ByteArrayOutputStream();
    entries.stream().sorted(Comparator.comparing(
        e -> treeEntryKey(e.mode(), e.name()))).forEach(e -> {
          out.writeBytes((e.mode() + " " + e.name() + "\0")
              .getBytes(ISO_8859_1));
          out.writeBytes(HexFormat.of().parseHex(e.oid()));
        });
    return out.toByteArray();
  }

  // (모드, blob 이름, 경로) → 뿌리 트리 이름.
  //
  // 경로를 '/' 로 나눠 디렉터리마다 트리를 짓고, 아래에서 위로 쓴다.
  // blob 이 저장소에 있는지는 보지 않는다(git write-tree 는 본다 —
  // 이 함수를 부르는 쪽이 인덱스에 올릴 때 이미 써 두었다).
  // O(항목 수 × 깊이 + 정렬).
  public static String writeTree(String gitdir, List<PathEntry> ents) {
    List<Entry> here = new ArrayList<>();
    Map<String, List<PathEntry>> subdirs = new LinkedHashMap<>();
    for (PathEntry e : ents) {
      int slash = e.path().indexOf('/');
      if (slash < 0) {
        here.add(new Entry(e.mode(), e.path(), e.oid()));
        continue;
      }
      subdirs.computeIfAbsent(e.path().substring(0, slash),
          k -> new ArrayList<>()).add(new PathEntry(e.mode(), e.oid(),
              e.path().substring(slash + 1)));
    }
    subdirs.forEach((name, sub) ->
        here.add(new Entry(DIR, name, writeTree(gitdir, sub))));
    return Objects.writeObject(gitdir, "tree", serializeTree(here));
  }

  // 트리를 재귀로 펼쳐 (모드, 이름, 경로). 하위 트리는 항목으로
  // 남기지 않고 그 안을 펼친다. 차례는 트리 차례이고, 전체 경로의
  // 바이트 차례와 같다(SPEC.md §4.3).
  public static List<PathEntry> flattenTree(String gitdir, String oid) {
    List<PathEntry> out = new ArrayList<>();
    flatten(gitdir, oid, "", out);
    return out;
  }

  private static void flatten(String gitdir, String oid, String prefix,
      List<PathEntry> out) {
    Objects.Obj o = Objects.readObject(gitdir, oid);
    if (!o.type().equals("tree")) {
      throw new GitError("fatal: mygit: " + oid + " is not a tree");
    }
    for (Entry e : parseTree(o.body())) {
      if (e.mode().equals(DIR)) {
        flatten(gitdir, e.oid(), prefix + e.name() + "/", out);
      } else {
        out.add(new PathEntry(e.mode(), e.oid(), prefix + e.name()));
      }
    }
  }

  // cat-file -p 가 찍는 형식 — 모드에서 정해진다.
  public static String typeOfMode(String mode) {
    return mode.equals(DIR) ? "tree"
        : mode.equals("160000") ? "commit" : "blob";
  }
}
