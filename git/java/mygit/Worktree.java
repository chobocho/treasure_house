package mygit;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.attribute.PosixFilePermission;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.TreeMap;
import java.util.TreeSet;

// 작업 트리 (SPEC.md §8 · §9.3) — 경로 따옴표, 훑기, status, 바꾸기.
//
// status 는 세 가지를 견준다: HEAD 트리, 인덱스, 디스크의 파일. 두 칸
// 글자(XY)가 곧 "어느 두 곳이 다른가" 다 — X 는 HEAD 와 인덱스, Y 는
// 인덱스와 작업 트리. 6부가 이 세 영역을 명령마다 캡처로 보인다.
public final class Worktree {
  private Worktree() {}

  // \a \b \t \n \v \f \r (7‥13)와 따옴표·역슬래시는 두 글자로 쓴다
  private static final String SHORT = "abtnvfr";

  // 경로 바이트 → git 이 사람에게 찍는 꼴 (core.quotePath=true).
  //
  // 제어 문자·DEL·따옴표·역슬래시·0x80 이상 바이트가 하나라도 있으면
  // 전체를 따옴표로 감싸고 C 식으로 쓴다(8진 세 자리). space 는
  // status 의 규칙 — 공백만 있어도 감싼다(공백 자체는 그대로).
  // 한글은 UTF-8 여섯 바이트가 \355\225… 로 찍힌다. O(경로 길이).
  public static String quotePath(String p, boolean space) {
    boolean need = space && p.contains(" ");
    StringBuilder body = new StringBuilder();
    for (char b : p.toCharArray()) {
      if (b == '"' || b == '\\') {
        body.append('\\').append(b);
      } else if (b >= 7 && b <= 13) {
        body.append('\\').append(SHORT.charAt(b - 7));
      } else if (b < 32 || b >= 127) {
        body.append(String.format("\\%03o", (int) b));
      } else {
        body.append(b);
        continue;
      }
      need = true;
    }
    return need ? "\"" + body + "\"" : body.toString();
  }

  public static String quotePath(String p) {
    return quotePath(p, false);
  }

  // 파일 하나의 모습 — 모드와 blob 이름. 인덱스 항목·트리 항목과
  // 같은 꼴이라 equals 로 곧장 견준다.
  public record Stat(int mode, String oid) {}

  // 작업 트리의 보통 파일 경로들, 전체 경로의 바이트 차례.
  //
  // 어느 깊이에서든 ".git" 은 건너뛰고, 심볼릭 링크와 장치 파일은
  // 없는 것으로 본다(SPEC.md §8.1). 빈 디렉터리는 아무것도 아니다.
  // O(파일 수 · log).
  public static List<String> walkWorktree(String root) {
    TreeSet<String> out = new TreeSet<>();
    visit(Path.of(root), "", out);
    return new ArrayList<>(out);
  }

  private static void visit(Path dir, String prefix, Set<String> out) {
    for (String name : Fs.list(dir.toString())) {
      Path p = dir.resolve(name);
      if (name.equals(".git")) continue;
      if (Files.isDirectory(p, LinkOption.NOFOLLOW_LINKS)) {
        visit(p, prefix + name + "/", out);
      } else if (Files.isRegularFile(p, LinkOption.NOFOLLOW_LINKS)) {
        out.add(prefix + name);
      }
    }
  }

  // 파일이 실행 파일인가 — 소유자 실행 비트만 본다(git 과 같다)
  static boolean isExec(Path p) {
    try {
      return Files.getPosixFilePermissions(p)
          .contains(PosixFilePermission.OWNER_EXECUTE);
    } catch (IOException e) {
      throw new UncheckedIOException(e);
    }
  }

  // (모드, blob 이름) 또는 파일이 없으면 null. 늘 해시한다 — stat
  // 캐시를 믿지 않으니 racy git 이 없다(SPEC.md §7.2).
  public static Stat fileState(String root, String path) {
    Path p = Path.of(root, path);
    if (!Files.isRegularFile(p, LinkOption.NOFOLLOW_LINKS)) return null;
    return new Stat(isExec(p) ? 0100755 : 0100644,
        Objects.hashObject("blob", Fs.read(p.toString())));
  }

  // 트리 → {경로: (모드, 이름)}, 경로 차례. 트리가 없으면(첫 커밋
  // 전) 빈 표.
  public static TreeMap<String, Stat> treeMap(String gitdir,
      String treeOid) {
    TreeMap<String, Stat> out = new TreeMap<>();
    if (treeOid == null) return out;
    for (Tree.PathEntry e : Tree.flattenTree(gitdir, treeOid)) {
      out.put(e.path(), new Stat(Integer.parseInt(e.mode(), 8),
          e.oid()));
    }
    return out;
  }

  // 충돌 경로의 두 글자 — 단계 1·2·3 이 있는가를 비트 0·1·2 로 놓은
  // 수가 자리 번호다(git 과 같다: 2·3 만 있으면 AA, 셋 다면 UU).
  private static final String[] UNMERGED =
      {"", "DD", "AU", "UD", "UA", "DU", "AA", "UU"};

  // 추적하지 않는 파일들을 git 의 normal 모드로 접는다(§8.3).
  //
  // 파일마다 위쪽 디렉터리부터 보며, 그 아래에 인덱스 항목이 하나도
  // 없는 첫 디렉터리가 있으면 "그 디렉터리/" 로 접는다.
  // O(파일 × 깊이).
  static List<String> untracked(List<String> files,
      Set<String> tracked) {
    Set<String> dirs = new HashSet<>();
    for (String t : tracked) {
      for (int i = t.indexOf('/'); i >= 0; i = t.indexOf('/', i + 1)) {
        dirs.add(t.substring(0, i));
      }
    }
    TreeSet<String> out = new TreeSet<>();
    for (String f : files) {
      if (tracked.contains(f)) continue;
      String shown = f;
      for (int i = f.indexOf('/'); i >= 0; i = f.indexOf('/', i + 1)) {
        if (!dirs.contains(f.substring(0, i))) {
          shown = f.substring(0, i + 1);
          break;
        }
      }
      out.add(shown);
    }
    return new ArrayList<>(out);
  }

  // git status --porcelain 과 같은 줄들(SPEC.md §8.3).
  //
  // X = HEAD 트리 ↔ 인덱스, Y = 인덱스 ↔ 작업 트리. 추적 중인 것을
  // 경로 차례로 먼저, 그다음 "?? " 줄들. O(파일 수 × 해시).
  public static List<String> status(String root, String gitdir) {
    String head = Refs.readHead(gitdir).oid();
    Map<String, Stat> base = treeMap(gitdir,
        head == null ? null : Refs.peel(gitdir, head, "tree"));
    Map<String, Stat> stage0 = new HashMap<>();
    Map<String, Integer> stages = new HashMap<>();
    for (Index.IndexEntry e : Index.readIndex(gitdir)) {
      if (e.stage == 0) stage0.put(e.path, new Stat(e.mode, e.oid));
      else stages.merge(e.path, 1 << (e.stage - 1), (a, b) -> a | b);
    }
    TreeSet<String> all = new TreeSet<>(base.keySet());
    all.addAll(stage0.keySet());
    all.addAll(stages.keySet());
    List<String> rows = new ArrayList<>();
    for (String p : all) {
      String xy;
      if (stages.containsKey(p)) {
        xy = UNMERGED[stages.get(p)];
      } else {
        Stat now = stage0.containsKey(p) ? fileState(root, p) : null;
        char x = !stage0.containsKey(p) ? 'D'
            : !base.containsKey(p) ? 'A'
            : stage0.get(p).equals(base.get(p)) ? ' ' : 'M';
        char y = !stage0.containsKey(p) ? ' ' : now == null ? 'D'
            : now.equals(stage0.get(p)) ? ' ' : 'M';
        xy = "" + x + y;
      }
      if (!xy.equals("  ")) rows.add(xy + " " + quotePath(p, true));
    }
    Set<String> tracked = new HashSet<>(stage0.keySet());
    tracked.addAll(stages.keySet());
    for (String p : untracked(walkWorktree(root), tracked)) {
      rows.add("?? " + quotePath(p, true));
    }
    return rows;
  }
}
