package mygit;

import static java.nio.charset.StandardCharsets.ISO_8859_1;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.FileAlreadyExistsException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.nio.file.StandardOpenOption;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;

// 참조 (SPEC.md §6) — 브랜치는 40글자가 든 파일 하나다.
//
// refs/heads/main 은 커밋 이름 한 줄이고, HEAD 는 보통 "ref: refs/
// heads/main" 이라는 이름표를 가리키는 이름표다. 커밋이 생기면 브랜치
// 파일의 한 줄이 바뀔 뿐이다 — 브랜치를 만드는 값이 싼 까닭이 이것이다.
//
// gc 뒤의 저장소는 참조를 packed-refs 한 파일에 모아 두므로 읽을 때는
// 둘 다 본다(느슨한 파일이 이긴다). 쓸 때는 느슨한 파일만 쓴다.
public final class Refs {
  public static final String ZERO = "0".repeat(40);

  private Refs() {}

  // 참조 파일 하나의 내용 — 심볼릭이면 대상 이름, 아니면 40글자
  public record Ref(boolean sym, String value) {}

  // HEAD — 가리키는 브랜치(분리면 null)와 커밋(태어나기 전이면 null)
  public record Head(String branch, String oid) {}

  public record Reflog(String old, String next, String ident,
      String message) {}

  private static String read(String path) {
    byte[] b = Fs.readOrNull(path);
    return b == null ? null : new String(b, ISO_8859_1);
  }

  // packed-refs → {이름: 40글자}. '#' 머리와 '^' 줄은 건너뛴다.
  public static Map<String, String> packedRefs(String gitdir) {
    Map<String, String> out = new TreeMap<>();
    String text = read(Fs.join(gitdir, "packed-refs"));
    for (String line : text == null ? new String[0]
        : text.split("\n")) {
      if (line.isEmpty() || "#^".indexOf(line.charAt(0)) >= 0) continue;
      String[] kv = line.split(" ", 2);
      out.put(kv[1], kv[0]);
    }
    return out;
  }

  // 참조 하나를 읽는다. 없으면 null. 느슨한 파일이 먼저다.
  public static Ref readRef(String gitdir, String name) {
    String text = read(Fs.join(gitdir, name));
    if (text != null) {
      text = text.strip();
      return text.startsWith("ref: ") ? new Ref(true, text.substring(5))
          : new Ref(false, text);
    }
    String oid = packedRefs(gitdir).get(name);
    return oid == null ? null : new Ref(false, oid);
  }

  // 심볼릭 참조를 따라가 40글자. 없거나 태어나지 않았으면 null.
  public static String resolveRef(String gitdir, String name) {
    for (int i = 0; i < 5; i++) {
      Ref r = readRef(gitdir, name);
      if (r == null) return null;
      if (!r.sym()) return r.value();
      name = r.value();
    }
    throw new GitError("fatal: mygit: symbolic ref loop at " + name);
  }

  public static Head readHead(String gitdir) {
    Ref r = readRef(gitdir, "HEAD");
    if (r == null) throw new GitError("fatal: mygit: HEAD is missing");
    return r.sym() ? new Head(r.value(), resolveRef(gitdir, r.value()))
        : new Head(null, r.value());
  }

  // prefix 아래 참조 {이름: 40글자}, 이름의 바이트 차례(TreeMap).
  public static TreeMap<String, String> listRefs(String gitdir,
      String prefix) {
    TreeMap<String, String> found = new TreeMap<>();
    packedRefs(gitdir).forEach((n, o) -> {
      if (n.startsWith(prefix)) found.put(n, o);
    });
    Path base = Path.of(gitdir, prefix);
    if (!Files.isDirectory(base)) return found;
    try (var s = Files.walk(base)) {
      for (Path p : s.filter(Files::isRegularFile).toList()) {
        String name = Path.of(gitdir).relativize(p).toString();
        String oid = name.endsWith(".lock") ? null
            : resolveRef(gitdir, name);
        if (oid != null) found.put(name, oid);
      }
    } catch (IOException e) {
      throw new UncheckedIOException(e);
    }
    return found;
  }

  public static TreeMap<String, String> listRefs(String gitdir) {
    return listRefs(gitdir, "refs/");
  }

  // <경로>.lock 에 쓰고 이름을 바꿔 넣는다(SPEC.md §6.1).
  private static void writeLocked(String path, String text) {
    Path p = Path.of(path);
    Path lock = Path.of(path + ".lock");
    try {
      Files.createDirectories(p.getParent());
      Files.write(lock, text.getBytes(ISO_8859_1),
          StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE);
      Files.move(lock, p, StandardCopyOption.REPLACE_EXISTING);
    } catch (FileAlreadyExistsException e) {
      throw new GitError("fatal: mygit: unable to lock " + path);
    } catch (IOException e) {
      throw new UncheckedIOException(e);
    }
  }

  // reflog 한 줄(SPEC.md §6.3) — "옛 새 신원<TAB>메시지".
  public static void appendReflog(String gitdir, String name,
      String old, String next, String ident, String message) {
    Path p = Path.of(gitdir, "logs", name);
    String line = (old == null ? ZERO : old) + " "
        + (next == null ? ZERO : next) + " " + ident + "\t" + message
        + "\n";
    try {
      Files.createDirectories(p.getParent());
      Files.write(p, line.getBytes(ISO_8859_1),
          StandardOpenOption.CREATE, StandardOpenOption.APPEND);
    } catch (IOException e) {
      throw new UncheckedIOException(e);
    }
  }

  // 오래된 것부터. 없으면 빈 목록.
  public static List<Reflog> readReflog(String gitdir, String name) {
    List<Reflog> out = new ArrayList<>();
    String text = read(Fs.join(gitdir, "logs", name));
    for (String line : text == null ? new String[0]
        : text.split("\n")) {
      if (line.isEmpty()) continue;
      String[] hm = line.split("\t", 2);
      String[] h = hm[0].split(" ", 3);
      out.add(new Reflog(h[0], h[1], h[2], hm.length > 1 ? hm[1] : ""));
    }
    return out;
  }

  // 참조 하나를 바꾸고 reflog 를 남긴다. next 가 null 이면 지운다.
  //
  // HEAD 가 이 브랜치를 가리키고 있으면 HEAD 의 reflog 에도 같은 줄을
  // 남긴다 — git 과 같다(커밋 하나가 두 로그에 모두 보이는 까닭).
  // packed-refs 에만 있는 참조를 지우는 일은 줄임이다(SPEC.md §6.1).
  public static void updateRef(String gitdir, String name, String next,
      String old, String message, String ident) {
    Path path = Path.of(gitdir, name);
    if (next == null) {
      try {
        if (!Files.deleteIfExists(path)) {
          throw new GitError("fatal: mygit: cannot delete packed ref "
              + name);
        }
        Files.deleteIfExists(Path.of(gitdir, "logs", name));
      } catch (IOException e) {
        throw new UncheckedIOException(e);
      }
      return;
    }
    writeLocked(path.toString(), next + "\n");
    appendReflog(gitdir, name, old, next, ident, message);
    Ref head = readRef(gitdir, "HEAD");
    if (!name.equals("HEAD") && new Ref(true, name).equals(head)) {
      appendReflog(gitdir, "HEAD", old, next, ident, message);
    }
  }

  // HEAD 를 브랜치(refs/heads/…)나 커밋(분리)으로. reflog 는 부르는
  // 쪽이 적는다 — 메시지가 명령마다 다르다(§6.3 의 표).
  public static void setHead(String gitdir, String target) {
    writeLocked(Fs.join(gitdir, "HEAD"),
        (target.startsWith("refs/") ? "ref: " : "") + target + "\n");
  }

  // ── 이름 풀기 (SPEC.md §6.2) ─────────────────────────────────────

  // 뒤붙이 없는 이름 → 40글자 또는 null. §6.2 의 1‥5 차례.
  private static String base(String gitdir, String name) {
    if (name.matches("[0-9a-f]{40}")
        && Objects.findObject(gitdir, name) != null) {
      return name;
    }
    if (List.of("HEAD", "ORIG_HEAD", "MERGE_HEAD").contains(name)) {
      return resolveRef(gitdir, name);
    }
    if (name.startsWith("refs/")) {
      String oid = resolveRef(gitdir, name);
      if (oid != null) return oid;
    }
    for (String cand : List.of("refs/tags/%s", "refs/heads/%s",
        "refs/remotes/%s", "refs/remotes/%s/HEAD")) {
      String oid = resolveRef(gitdir, cand.formatted(name));
      if (oid != null) return oid;
    }
    try {
      return Objects.findObject(gitdir, name);
    } catch (GitError e) {
      return null;                     // 모호한 앞부분은 풀지 못한 것
    }
  }

  // 태그를 벗겨 want("commit"·"tree")를 얻는다. 못 얻으면 null.
  public static String peel(String gitdir, String oid, String want) {
    for (int i = 0; i < 10; i++) {
      Objects.Obj o = Objects.readObject(gitdir, oid);
      if (o.type().equals(want)) return oid;
      String first = new String(o.body(), 0, Math.min(47,
          o.body().length), ISO_8859_1);
      if (o.type().equals("tag")) {
        oid = first.substring(7, 47);
      } else if (o.type().equals("commit") && want.equals("tree")) {
        oid = first.substring(5, 45);
      } else {
        return null;
      }
    }
    return null;
  }

  private static List<String> parents(String gitdir, String oid) {
    return Commit.parseCommit(Objects.readObject(gitdir, oid).body())
        .parents();
  }

  // <rev> → 40글자 또는 null. ~n · ^n · ^0 · ^{tree} · ^{commit}.
  //
  // 뒤붙이는 왼쪽부터 차례로 적용한다. O(뒤붙이의 길이 × 객체 읽기).
  public static String revParse(String gitdir, String spec) {
    int i = 0;
    while (i < spec.length() && "~^".indexOf(spec.charAt(i)) < 0) i++;
    String oid = i > 0 ? base(gitdir, spec.substring(0, i)) : null;
    while (oid != null && i < spec.length()) {
      char op = spec.charAt(i++);
      if (op == '^' && spec.startsWith("{", i)) {
        int end = spec.indexOf('}', i);
        String want = spec.substring(i + 1, end);
        i = end + 1;
        oid = peel(gitdir, oid, want.isEmpty() ? "commit" : want);
        continue;
      }
      int j = i;
      while (j < spec.length() && Character.isDigit(spec.charAt(j))) {
        j++;
      }
      int n = j > i ? Integer.parseInt(spec.substring(i, j)) : 1;
      i = j;
      oid = peel(gitdir, oid, "commit");
      if (oid == null) return null;
      if (op == '~') {
        for (int k = 0; k < n && oid != null; k++) {
          List<String> ps = parents(gitdir, oid);
          oid = ps.isEmpty() ? null : ps.get(0);
        }
      } else if (n > 0) {
        List<String> ps = parents(gitdir, oid);
        oid = n <= ps.size() ? ps.get(n - 1) : null;
      }
    }
    return oid;
  }

  // SPEC.md §9.2 의 브랜치 이름 규칙(check-ref-format 의 일부).
  public static boolean validBranchName(String name) {
    if (name.isEmpty() || name.equals("@") || name.contains("..")
        || name.contains("@{") || name.contains("//")) {
      return false;
    }
    for (char c : name.toCharArray()) {
      if (" ~^:?*[\\".indexOf(c) >= 0 || c < 32 || c == 127) {
        return false;
      }
    }
    return "-./".indexOf(name.charAt(0)) < 0 && !name.endsWith("/")
        && !name.endsWith(".") && !name.endsWith(".lock");
  }
}
