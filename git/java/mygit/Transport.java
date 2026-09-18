package mygit;

import static java.nio.charset.StandardCharsets.ISO_8859_1;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.io.UncheckedIOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.HexFormat;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

// 전송 (SPEC.md §14) — 저장소끼리 객체와 참조를 나누는 법.
//
// pkt-line 은 "길이 네 자리 16진 + 데이터" 다. 길이가 자기 4바이트를
// 품는 까닭은 0000(flush)·0001(delim) 같은 특별한 값을 데이터와
// 헷갈리지 않게 하려는 것이다. 여기에는 두 가지가 있다: 협상 없이 객체
// 파일을 그대로 복사하는 "멍청한" 로컬 clone, 그리고 진짜 git
// upload-pack 을 자식으로 띄워 프로토콜 v2 로 말하는 fetch-pack(서버는
// 짜지 않는다 — PLAN.md §9 결정 8).
public final class Transport {
  static final String FLUSH = "0000";
  static final String DELIM = "0001";

  private Transport() {}

  // 데이터 → pkt-line 한 개.
  public static byte[] pktLine(byte[] data) {
    if (data.length > 65516) {
      throw new GitError("fatal: mygit: pkt-line too long");
    }
    byte[] out = Arrays.copyOf(String.format("%04x", data.length + 4)
        .getBytes(ISO_8859_1), data.length + 4);
    System.arraycopy(data, 0, out, 4, data.length);
    return out;
  }

  // 대화 기록의 꼴(SPEC.md §14.3) — 길이 + 파이썬 repr 식 이스케이프.
  //
  // repr 은 작은따옴표로 감싸되, 데이터에 작은따옴표만 있고 큰따옴표가
  // 없으면 큰따옴표로 감싼다. 감싼 따옴표와 역슬래시만 이스케이프하고,
  // \t \n \r 은 두 글자, 그 밖의 인쇄 못 할 바이트는 \xhh 다.
  public static String render(byte[] data) {
    String s = new String(data, ISO_8859_1);
    char quote = s.contains("'") && !s.contains("\"") ? '"' : '\'';
    StringBuilder out = new StringBuilder(
        String.format("%04x", data.length + 4));
    for (char b : s.toCharArray()) {
      if (b == '\\' || b == quote) out.append('\\').append(b);
      else if (b == '\t') out.append("\\t");
      else if (b == '\n') out.append("\\n");
      else if (b == '\r') out.append("\\r");
      else if (b < 32 || b >= 127) out.append(String.format("\\x%02x",
          (int) b));
      else out.append(b);
    }
    return out.toString();
  }

  // ── 멍청한 로컬 clone (SPEC.md §14.2) ─────────────────────────────

  private static String srcGitdir(String src) {
    String g = Fs.join(src, ".git");
    return Fs.isDir(g) ? g : src;
  }

  private static void append(String path, String text) {
    try {
      Files.write(Path.of(path), text.getBytes(ISO_8859_1),
          StandardOpenOption.APPEND);
    } catch (IOException e) {
      throw new UncheckedIOException(e);
    }
  }

  // src 의 객체 파일을 그대로 복사하고 참조를 세운다. → 브랜치 이름.
  //
  // 협상이 없다 — 받는 쪽이 이미 가진 것도 다시 복사한다. 그래도
  // 객체의 이름이 곧 내용이므로 옮긴 파일은 어느 저장소에서나 같은
  // 객체다. src 는 절대 경로다.
  public static String cloneLocal(String src, String dst,
      String ident) {
    String sg = srcGitdir(src);
    String g = Fs.join(dst, ".git");
    Path objs = Path.of(sg, "objects");
    try (var s = Files.walk(objs)) {
      for (Path p : s.filter(Files::isRegularFile).toList()) {
        String rel = Path.of(sg).relativize(p).toString();
        String name = p.getFileName().toString();
        if (p.getParent().endsWith("pack") && !name.endsWith(".pack")
            && !name.endsWith(".idx")) {
          continue;
        }
        Path to = Path.of(g, rel);
        Files.createDirectories(to.getParent());
        Files.copy(p, to);
      }
    } catch (IOException e) {
      throw new UncheckedIOException(e);
    }
    Refs.Ref head = Refs.readRef(sg, "HEAD");
    Refs.listRefs(sg).forEach((name, oid) -> {
      String local = name.startsWith("refs/heads/")
          ? "refs/remotes/origin/" + name.substring(11)
          : name.startsWith("refs/tags/") ? name : null;
      if (local != null) {
        Fs.mkdirs(Path.of(g, local).getParent().toString());
        Fs.write(Fs.join(g, local), (oid + "\n").getBytes(ISO_8859_1));
      }
    });
    if (!head.sym()) {
      throw new GitError("fatal: mygit: source HEAD is detached");
    }
    String branch = head.value().substring("refs/heads/".length());
    Fs.mkdirs(Fs.join(g, "refs", "remotes", "origin"));
    Fs.write(Fs.join(g, "refs", "remotes", "origin", "HEAD"),
        ("ref: refs/remotes/origin/" + branch + "\n")
            .getBytes(ISO_8859_1));
    String oid = Refs.resolveRef(sg, head.value());
    Refs.setHead(g, head.value());
    Refs.updateRef(g, head.value(), oid, null, "clone: from " + src,
        ident);
    append(Fs.join(g, "config"), "[remote \"origin\"]\n\turl = " + src
        + "\n\tfetch = +refs/heads/*:refs/remotes/origin/*\n"
        + "[branch \"" + branch + "\"]\n\tremote = origin\n"
        + "\tmerge = refs/heads/" + branch + "\n");
    Worktree.checkoutTree(dst, g, null, Refs.peel(g, oid, "tree"));
    return branch;
  }

  // ── fetch-pack: 프로토콜 v2 (SPEC.md §14.3) ───────────────────────

  // 자식 upload-pack 과의 pkt-line 대화. 기록은 SPEC §14.3 의 꼴.
  private static final class Wire {
    final Process p;
    final OutputStream in;
    final InputStream out;
    final List<String> log = new ArrayList<>();

    Wire(String src, Map<String, String> env) {
      ProcessBuilder pb = new ProcessBuilder("git", "upload-pack", src);
      pb.environment().clear();
      pb.environment().putAll(env);
      pb.environment().put("GIT_PROTOCOL", "version=2");
      pb.redirectError(ProcessBuilder.Redirect.INHERIT);
      try {
        p = pb.start();
      } catch (IOException e) {
        throw new UncheckedIOException(e);
      }
      in = p.getOutputStream();
      out = p.getInputStream();
    }

    // 문자열 하나는 패킷 하나 — FLUSH·DELIM 은 그대로 보낸다
    void send(List<String> items) {
      ByteArrayOutputStream buf = new ByteArrayOutputStream();
      for (String it : items) {
        byte[] d = it.getBytes(ISO_8859_1);
        boolean special = it.equals(FLUSH) || it.equals(DELIM);
        log.add("> " + (special ? it : render(d)));
        buf.writeBytes(special ? d : pktLine(d));
      }
      try {
        in.write(buf.toByteArray());
        in.flush();
      } catch (IOException e) {
        throw new UncheckedIOException(e);
      }
    }

    byte[] exact(int n) {
      try {
        byte[] data = out.readNBytes(n);
        if (data.length != n) {
          throw new GitError("fatal: mygit: remote hung up "
              + "unexpectedly");
        }
        return data;
      } catch (IOException e) {
        throw new UncheckedIOException(e);
      }
    }

    // flush 까지의 패킷들. packfile 절 뒤의 사이드밴드 1 은 pack 으로
    // 모은다(2 는 진행 안내, 3 은 원격의 오류).
    List<String> read(ByteArrayOutputStream pack) {
      List<String> lines = new ArrayList<>();
      boolean side = false;
      for (;;) {
        int n = Integer.parseInt(new String(exact(4), ISO_8859_1), 16);
        if (n < 4) {
          log.add(String.format("< %04x", n));
          if (n == 0) return lines;
          continue;
        }
        byte[] data = exact(n - 4);
        if (side && data[0] == 1) {
          pack.write(data, 1, data.length - 1);
          log.add(String.format("< %04x [pack %d bytes]", n, n - 5));
          continue;
        }
        if (side && data[0] == 3) {
          throw new GitError("fatal: mygit: remote error: "
              + new String(data, 1, data.length - 1, ISO_8859_1));
        }
        log.add("< " + render(data));
        String line = new String(data, ISO_8859_1);
        side = side || (line.equals("packfile\n") && pack != null);
        lines.add(line);
      }
    }

    void close(String logPath) {
      try {
        in.close();
        p.waitFor();
      } catch (IOException e) {
        throw new UncheckedIOException(e);
      } catch (InterruptedException e) {
        Thread.currentThread().interrupt();
      }
      if (logPath != null) {
        Fs.write(logPath, (String.join("\n", log) + "\n")
            .getBytes(ISO_8859_1));
      }
    }
  }

  // 받은 참조 하나 — 이름과 값
  public record Got(String oid, String name) {}

  // wantRefs 를 받아 팩을 저장한다. 참조는 고치지 않는다 — 그것은
  // fetch 의 일이다(SPEC.md §14.3 의 5).
  public static List<Got> fetchPack(String gitdir, String src,
      List<String> wantRefs, Map<String, String> env, String logPath) {
    Wire w = new Wire(src, env);
    List<String> caps = w.read(null);
    if (caps.isEmpty() || !caps.get(0).equals("version 2\n")
        || caps.stream().noneMatch(c -> c.startsWith("fetch"))) {
      throw new GitError("fatal: mygit: server does not speak "
          + "protocol v2");
    }
    List<String> req = new ArrayList<>(List.of("command=ls-refs\n",
        "object-format=sha1\n", DELIM, "peel\n", "symrefs\n"));
    wantRefs.forEach(r -> req.add("ref-prefix " + r + "\n"));
    req.add(FLUSH);
    w.send(req);
    Map<String, String> adv = new HashMap<>();
    for (String line : w.read(null)) {
      String[] cols = line.strip().split(" ");
      adv.put(cols[1], cols[0]);
    }
    Set<String> wants = new LinkedHashSet<>();
    for (String r : wantRefs) {
      if (!adv.containsKey(r)) {
        throw new GitError("fatal: mygit: no such remote ref " + r);
      }
      wants.add(adv.get(r));
    }
    List<String> fetch = new ArrayList<>(List.of("command=fetch\n",
        "object-format=sha1\n", DELIM, "ofs-delta\n", "no-progress\n"));
    wants.forEach(o -> fetch.add("want " + o + "\n"));
    new LinkedHashSet<>(Refs.listRefs(gitdir).values())
        .forEach(o -> fetch.add("have " + o + "\n"));
    fetch.add("done\n");
    fetch.add(FLUSH);
    w.send(fetch);
    ByteArrayOutputStream buf = new ByteArrayOutputStream();
    w.read(buf);
    w.close(logPath);
    byte[] data = buf.toByteArray();
    List<Pack.PackEntry> ents = Pack.readPack(data,
        o -> Objects.readObject(gitdir, o));
    byte[] sum = Arrays.copyOfRange(data, data.length - 20,
        data.length);
    String stem = Fs.join(gitdir, "objects", "pack",
        "pack-" + HexFormat.of().formatHex(sum));
    Fs.mkdirs(Path.of(stem).getParent().toString());
    Fs.write(stem + ".pack", data);
    Fs.write(stem + ".idx", Pack.writeIdx(ents, sum));
    return wantRefs.stream().map(r -> new Got(adv.get(r), r)).toList();
  }
}
