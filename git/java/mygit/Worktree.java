package mygit;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.attribute.PosixFilePermission;
import java.nio.file.attribute.PosixFilePermissions;
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

  static final String OVERWRITE = "error: Your local changes to the "
      + "following files would be overwritten by checkout:";
  static final String UNTRACKED = "error: The following untracked "
      + "working tree files would be overwritten by checkout:";

  // 파일 하나를 쓴다. 0666/0777 로 만들고 umask 를 따른다 — git 과
  // 같다(SPEC.md §9.3). 있던 파일은 지우고 새로 만든다 — 그래야 실행
  // 비트가 새 모드를 따른다.
  static void writeFile(String root, String path, int mode,
      byte[] data) {
    Path p = Path.of(root, path);
    try {
      Files.createDirectories(p.getParent());
      Files.deleteIfExists(p);
      if ((mode & 0100) != 0) {
        Files.createFile(p, PosixFilePermissions.asFileAttribute(
            PosixFilePermissions.fromString("rwxrwxrwx")));
      }
      Files.write(p, data);
    } catch (IOException e) {
      throw new UncheckedIOException(e);
    }
  }

  // 파일을 지우고, 그래서 비게 된 디렉터리들도 지운다.
  static void removeFile(String root, String path) {
    Path base = Path.of(root);
    Path p = base.resolve(path);
    try {
      Files.deleteIfExists(p);
      for (Path d = p.getParent(); !d.equals(base)
          && Fs.list(d.toString()).isEmpty(); d = d.getParent()) {
        Files.delete(d);
      }
    } catch (IOException e) {
      throw new UncheckedIOException(e);
    }
  }

  // 두 갈래 합치기로 작업 트리·인덱스를 old → new 로(SPEC.md §9.3).
  //
  // 경로마다: 옛 트리와 새 트리에서 같으면 손대지 않는다(손댄 내용이
  // 따라온다). 다르면 인덱스가 옛 트리와 같고 작업 트리가 인덱스와
  // 같아야 한다. 옛 트리에 없던 경로에 추적 안 하는 파일이 있으면
  // 그것도 막는다. 하나라도 걸리면 아무것도 바꾸지 않고 멈춘다.
  // O(경로 수 × 해시).
  public static void checkoutTree(String root, String gitdir,
      String oldTree, String newTree) {
    Map<String, Stat> old = treeMap(gitdir, oldTree);
    Map<String, Stat> nu = treeMap(gitdir, newTree);
    List<Index.IndexEntry> ents = Index.readIndex(gitdir);
    Map<String, Index.IndexEntry> idx = new HashMap<>();
    Set<String> unmerged = new HashSet<>();
    for (Index.IndexEntry e : ents) {
      if (e.stage == 0) idx.put(e.path, e);
      else unmerged.add(e.path);
    }
    TreeSet<String> changed = new TreeSet<>(old.keySet());
    changed.addAll(nu.keySet());
    changed.removeIf(p -> java.util.Objects.equals(old.get(p),
        nu.get(p)));
    List<String> local = new ArrayList<>();
    List<String> stray = new ArrayList<>();
    for (String p : changed) {
      Index.IndexEntry e = idx.get(p);
      Stat cur = e == null ? null : new Stat(e.mode, e.oid);
      Stat disk = fileState(root, p);
      if (unmerged.contains(p)) {
        local.add(p);
      } else if (cur == null && old.get(p) == null) {
        if (disk != null && nu.get(p) != null) stray.add(p);
      } else if (!java.util.Objects.equals(cur, old.get(p))
          || !java.util.Objects.equals(disk, cur)) {
        local.add(p);
      }
    }
    if (!local.isEmpty() || !stray.isEmpty()) {
      StringBuilder sb = new StringBuilder();
      for (var group : List.of(Map.entry(OVERWRITE, local),
          Map.entry(UNTRACKED, stray))) {
        if (group.getValue().isEmpty()) continue;
        sb.append(group.getKey()).append('\n');
        group.getValue().forEach(q ->
            sb.append('\t').append(quotePath(q)).append('\n'));
        sb.append('\n');
      }
      throw new GitError(sb + "Aborting", 1);
    }
    for (String p : changed) {
      Stat n = nu.get(p);
      if (n == null) {
        removeFile(root, p);
        idx.remove(p);
        continue;
      }
      writeFile(root, p, n.mode(),
          Objects.readObject(gitdir, n.oid()).body());
      idx.put(p, Index.entryFromStat(p, Fs.join(root, p), n.oid()));
    }
    Index.writeIndex(gitdir, new ArrayList<>(idx.values()));
  }

  // 바꾼 뒤 남은 변경 — "M\t경로" 줄들(SPEC.md §9.3 끝).
  //
  // 새 HEAD 트리와 견주어 인덱스나 작업 트리가 다른 추적 경로. M 은
  // 내용·모드, D 는 작업 트리에 없음, A 는 인덱스에만 있음.
  public static List<String> localChanges(String root, String gitdir,
      String headTree) {
    Map<String, Stat> head = treeMap(gitdir, headTree);
    List<String> rows = new ArrayList<>();
    for (Index.IndexEntry e : Index.readIndex(gitdir)) {
      if (e.stage != 0) continue;
      Stat st = new Stat(e.mode, e.oid);
      Stat disk = fileState(root, e.path);
      char letter = disk == null ? 'D' : !head.containsKey(e.path) ? 'A'
          : !st.equals(head.get(e.path)) || !st.equals(disk) ? 'M' : 0;
      if (letter != 0) rows.add(letter + "\t" + quotePath(e.path));
    }
    return rows;
  }
}
