package mygit;

import static java.nio.charset.StandardCharsets.ISO_8859_1;
import static java.nio.charset.StandardCharsets.UTF_8;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.TreeMap;
import java.util.TreeSet;

// 명령줄 (SPEC.md §1 · §9) — 인자를 읽고, 모듈을 부르고, 찍는다.
//
// 출력은 이 클래스만 한다. 다른 모듈은 값을 돌려주거나 GitError 를
// 던질 뿐이다 — 그래야 시험이 출력을 가로채지 않고 반환값을 본다.
// run() 은 과정 안에서 부를 수 있는 꼴(코드, 표준 출력, 표준 오류)
// 이고, Main 이 그것을 진짜 표준 스트림에 잇는다.
//
// 안의 문자열은 전부 "바이트 문자열"(latin1)이다 — 인자·환경 변수는
// run 의 입구에서 UTF-8 바이트로 바꾸고, 찍을 때 latin1 로 되돌린다.
// 그래서 한글 경로도 커밋 메시지도 바이트 그대로 지나간다.
public final class Cli {
  private Cli() {}

  public record Result(int code, byte[] out, byte[] err) {}

  private interface Command {
    int run(Ctx ctx, List<String> args);
  }

  static final String NOT_A_REPO = "fatal: not a git repository (or "
      + "any of the parent directories): .git";

  // 유니코드 문자열 → 바이트 문자열(UTF-8 바이트를 한 글자씩)
  public static String bytes(String s) {
    return new String(s.getBytes(UTF_8), ISO_8859_1);
  }

  // 명령 하나가 도는 동안의 문맥 — 현재 디렉터리·환경·입출력.
  public static final class Ctx {
    final String cwd;
    final Map<String, String> env = new HashMap<>();
    final ByteArrayOutputStream out = new ByteArrayOutputStream();
    final ByteArrayOutputStream err = new ByteArrayOutputStream();
    private byte[] stdin;
    private String top;

    public Ctx(String cwd, Map<String, String> env, byte[] stdin) {
      this.cwd = Path.of(cwd).toAbsolutePath().normalize().toString();
      env.forEach((k, v) -> this.env.put(k, bytes(v)));
      this.stdin = stdin;
    }

    // 표준 입력 전부. 필요한 명령(--stdin)만 부른다 — 늘 읽으면
    // 입력이 닫히지 않은 파이프에서 부를 때 멈춘다.
    byte[] readStdin() {
      try {
        if (stdin == null) stdin = System.in.readAllBytes();
        return stdin;
      } catch (IOException e) {
        throw new UncheckedIOException(e);
      }
    }

    void say(String text) {
      out.writeBytes(text.getBytes(ISO_8859_1));
    }

    void say(byte[] data) {
      out.writeBytes(data);
    }

    void warn(String text) {
      err.writeBytes(text.getBytes(ISO_8859_1));
    }

    // 작업 트리의 뿌리 — .git 을 품은 디렉터리(SPEC.md §1.1).
    //
    // 현재 디렉터리부터 위로 올라가며 .git 을 찾는다.
    // GIT_CEILING_DIRECTORIES 에 적힌 디렉터리 안으로는 올라가지
    // 않는다 — 현재 디렉터리 자신은 언제나 본다. O(깊이).
    String root() {
      if (top != null) return top;
      Set<Path> ceil = new HashSet<>();
      for (String p : env.getOrDefault("GIT_CEILING_DIRECTORIES", "")
          .split(":")) {
        if (!p.isEmpty()) ceil.add(Path.of(p).toAbsolutePath());
      }
      for (Path d = Path.of(cwd);; d = d.getParent()) {
        if (Fs.isDir(Fs.join(d.toString(), ".git"))) {
          return top = d.toString();
        }
        if (d.getParent() == null || ceil.contains(d.getParent())) {
          throw new GitError(NOT_A_REPO);
        }
      }
    }

    public String gitdir() {
      return Fs.join(root(), ".git");
    }

    // 명령줄의 경로 → 절대 경로(현재 디렉터리 기준).
    String path(String name) {
      return Path.of(cwd).resolve(name).normalize().toString();
    }
  }

  // <rev> → 객체 이름. 없으면 null (SPEC.md §6.2).
  static String resolve(Ctx ctx, String name) {
    return Refs.revParse(ctx.gitdir(), name);
  }

  // <rev> → 태그를 벗긴 want("commit"·"tree"). 없으면 null.
  static String resolve(Ctx ctx, String name, String want) {
    String oid = resolve(ctx, name);
    return oid == null ? null : Refs.peel(ctx.gitdir(), oid, want);
  }

  static final String AMBIGUOUS = "fatal: ambiguous argument '%s': "
      + "unknown revision or path not in the working tree.\n"
      + "Use '--' to separate paths from revisions, like this:\n"
      + "'git <command> [<revision>...] -- [<file>...]'";

  static String ident(Ctx ctx, String who) {
    return Commit.identFromEnv(ctx.env, who);
  }

  static String ident(Ctx ctx) {
    return ident(ctx, "COMMITTER");
  }

  // 옵션을 읽은 결과 — 켜진 짧은 옵션, 값 옵션, 나머지 인자.
  record Flags(Set<String> on, Map<String, String> vals,
      List<String> rest) {}

  // 모르는 옵션은 SPEC.md §1.4 의 "unknown option" 오류다. '--'
  // 뒤는 전부 인자로 본다.
  static Flags parseFlags(List<String> args, List<String> flags,
      String... valued) {
    Flags f = new Flags(new HashSet<>(), new HashMap<>(),
        new ArrayList<>());
    for (int i = 0; i < args.size(); i++) {
      String a = args.get(i);
      if (a.equals("--")) {
        f.rest.addAll(args.subList(i + 1, args.size()));
        break;
      }
      if (List.of(valued).contains(a)) {
        if (i + 1 == args.size()) {
          throw new GitError("fatal: mygit: option '" + a
              + "' needs a value");
        }
        f.vals.put(a, args.get(++i));
      } else if (flags.contains(a)) {
        f.on.add(a);
      } else if (a.startsWith("-") && !a.equals("-")) {
        throw new GitError("fatal: mygit: unknown option '" + a + "'");
      } else {
        f.rest.add(a);
      }
    }
    return f;
  }

  // ── 3단계: hash-object · cat-file ─────────────────────────────────
  static int hashObject(Ctx ctx, List<String> args) {
    Flags f = parseFlags(args, List.of("-w", "--stdin"), "-t");
    String type = f.vals.getOrDefault("-t", "blob");
    if (!Objects.TYPES.contains(type)) {
      throw new GitError("fatal: mygit: unknown object type '" + type
          + "'");
    }
    List<byte[]> bodies = f.on.contains("--stdin")
        ? List.of(ctx.readStdin())
        : f.rest.stream().map(n -> readArg(ctx, n)).toList();
    for (byte[] body : bodies) {
      ctx.say((f.on.contains("-w")
          ? Objects.writeObject(ctx.gitdir(), type, body)
          : Objects.hashObject(type, body)) + "\n");
    }
    return 0;
  }

  // 명령줄이 가리키는 파일 전부. 못 읽으면 git 과 같은 문장 —
  // libc 의 strerror 를 Java 의 예외 종류에서 되짚는다(SPEC.md §1.4).
  static byte[] readArg(Ctx ctx, String name) {
    try {
      return java.nio.file.Files.readAllBytes(Path.of(ctx.path(name)));
    } catch (IOException e) {
      String why = e instanceof java.nio.file.NoSuchFileException
          ? "No such file or directory"
          : e instanceof java.nio.file.AccessDeniedException
          ? "Permission denied" : "Is a directory";
      throw new GitError("fatal: could not open '" + name
          + "' for reading: " + why);
    }
  }

  // cat-file -p 의 몸. blob·commit·tag 는 그대로, 트리는 항목마다
  // "%06o 형식 이름\t경로" (SPEC.md §9, 경로 따옴표는 §8.2).
  static byte[] pretty(String type, byte[] body) {
    if (!type.equals("tree")) return body;
    StringBuilder sb = new StringBuilder();
    for (Tree.Entry e : Tree.parseTree(body)) {
      sb.append(String.format("%06o %s %s\t%s\n",
          Integer.parseInt(e.mode(), 8), Tree.typeOfMode(e.mode()),
          e.oid(), Worktree.quotePath(e.name())));
    }
    return sb.toString().getBytes(ISO_8859_1);
  }

  static int catFile(Ctx ctx, List<String> args) {
    Flags f = parseFlags(args, List.of("-t", "-s", "-p"));
    if (f.on.size() != 1 || f.rest.size() != 1) {
      throw new GitError("usage: mygit cat-file (-t | -s | -p) "
          + "<object>", 129);
    }
    String oid = resolve(ctx, f.rest.get(0));
    if (oid == null) {
      throw new GitError("fatal: Not a valid object name "
          + f.rest.get(0));
    }
    Objects.Obj o = Objects.readObject(ctx.gitdir(), oid);
    if (f.on.contains("-t")) ctx.say(o.type() + "\n");
    else if (f.on.contains("-s")) ctx.say(o.body().length + "\n");
    else ctx.say(pretty(o.type(), o.body()));
    return 0;
  }

  // ── 5단계: init · commit-tree · branch · tag · reflog ────────────
  static final String CONFIG = "[core]\n"
      + "\trepositoryformatversion = 0\n\tfilemode = true\n"
      + "\tbare = false\n\tlogallrefupdates = true\n";
  static final String HEADS = "refs/heads/";

  // top/.git 을 SPEC.md §5.1 의 꼴로. 이미 있었으면 true.
  static boolean makeRepo(String top) {
    String g = Fs.join(top, ".git");
    boolean again = Fs.isDir(g);
    for (String d : List.of("objects/pack", HEADS, "refs/tags")) {
      Fs.mkdirs(Fs.join(g, d));
    }
    Map.of("HEAD", "ref: refs/heads/main\n", "config", CONFIG)
        .forEach((name, text) -> {
          String p = Fs.join(g, name);
          if (!Fs.exists(p)) Fs.write(p, text.getBytes(ISO_8859_1));
        });
    return again;
  }

  // SPEC.md §5.1 — 이미 있으면 아무것도 덮어쓰지 않는다.
  static int init(Ctx ctx, List<String> args) {
    List<String> rest = parseFlags(args, List.of()).rest;
    String top = rest.isEmpty() ? ctx.cwd : ctx.path(rest.get(0));
    boolean again = makeRepo(top);
    ctx.say((again ? "Reinitialized existing" : "Initialized empty")
        + " Git repository in " + Fs.join(top, ".git") + "/\n");
    return 0;
  }

  // -p 와 -m 은 몇 번이든, 준 차례대로. 메시지는 원문 그대로 +
  // 줄바꿈 — 공백 정리는 commit 명령만 한다(SPEC.md §4.4).
  static int commitTree(Ctx ctx, List<String> args) {
    String treeArg = null;
    List<String> parents = new ArrayList<>();
    List<String> msgs = new ArrayList<>();
    for (int i = 0; i < args.size(); i++) {
      String a = args.get(i);
      if (a.equals("-p") || a.equals("-m")) {
        if (++i == args.size()) {
          throw new GitError("fatal: mygit: option '" + a
              + "' needs a value");
        }
        String val = args.get(i);
        if (a.equals("-m")) {
          msgs.add(val);
          continue;
        }
        String oid = resolve(ctx, val);
        if (oid == null) {
          throw new GitError("fatal: not a valid object name " + val);
        }
        parents.add(oid);
      } else if (a.startsWith("-")) {
        throw new GitError("fatal: mygit: unknown option '" + a + "'");
      } else {
        treeArg = a;
      }
    }
    if (treeArg == null || msgs.isEmpty()) {
      throw new GitError("usage: mygit commit-tree <tree> "
          + "[-p <parent>]... -m <message>...", 129);
    }
    String t = resolve(ctx, treeArg, "tree");
    if (t == null) {
      throw new GitError("fatal: not a valid object name " + treeArg);
    }
    byte[] body = Commit.serializeCommit(t, parents,
        ident(ctx, "AUTHOR"), ident(ctx),
        String.join("\n\n", msgs) + "\n");
    ctx.say(Objects.writeObject(ctx.gitdir(), "commit", body) + "\n");
    return 0;
  }

  static int listBranches(Ctx ctx) {
    Refs.Head h = Refs.readHead(ctx.gitdir());
    if (h.branch() == null && h.oid() != null) {
      ctx.say("* (HEAD detached at " + h.oid().substring(0, 7) + ")\n");
    }
    for (String name : Refs.listRefs(ctx.gitdir(), HEADS).keySet()) {
      ctx.say((name.equals(h.branch()) ? "* " : "  ")
          + name.substring(HEADS.length()) + "\n");
    }
    return 0;
  }

  static int branch(Ctx ctx, List<String> args) {
    Flags f = parseFlags(args, List.of("-d"));
    if (f.on.contains("-d")) return deleteBranch(ctx, f.rest);
    if (f.rest.isEmpty()) return listBranches(ctx);
    String name = f.rest.get(0);
    String g = ctx.gitdir();
    if (!Refs.validBranchName(name)) {
      throw new GitError("fatal: '" + name
          + "' is not a valid branch name");
    }
    if (Refs.resolveRef(g, HEADS + name) != null) {
      throw new GitError("fatal: a branch named '" + name
          + "' already exists");
    }
    String start = f.rest.size() > 1 ? f.rest.get(1) : "HEAD";
    String oid = resolve(ctx, start, "commit");
    if (oid == null) {
      throw new GitError("fatal: not a valid object name: '" + start
          + "'");
    }
    Refs.updateRef(g, HEADS + name, oid, null,
        "branch: Created from " + start, ident(ctx));
    return 0;
  }

  // branch -d — HEAD 에서 닿는 브랜치만 지운다(SPEC.md §9.2).
  static int deleteBranch(Ctx ctx, List<String> names) {
    String g = ctx.gitdir();
    Refs.Head h = Refs.readHead(g);
    for (String name : names) {
      String ref = HEADS + name;
      String oid = Refs.resolveRef(g, ref);
      if (ref.equals(h.branch())) {
        throw new GitError("error: cannot delete branch '" + name
            + "' used by worktree at '" + ctx.root() + "'", 1);
      }
      if (oid == null) {
        throw new GitError("error: branch '" + name + "' not found.",
            1);
      }
      if (h.oid() == null || !Walk.isAncestor(g, oid, h.oid())) {
        throw new GitError("error: the branch '" + name
            + "' is not fully merged", 1);
      }
      Refs.updateRef(g, ref, null, oid, "", "");
      ctx.say("Deleted branch " + name + " (was " + oid.substring(0, 7)
          + ").\n");
    }
    return 0;
  }

  static int tag(Ctx ctx, List<String> args) {
    Flags f = parseFlags(args, List.of("-a"), "-m");
    String g = ctx.gitdir();
    if (f.rest.isEmpty()) {
      for (String name : Refs.listRefs(g, "refs/tags/").keySet()) {
        ctx.say(name.substring("refs/tags/".length()) + "\n");
      }
      return 0;
    }
    String name = f.rest.get(0);
    String target = f.rest.size() > 1 ? f.rest.get(1) : "HEAD";
    if (Refs.readRef(g, "refs/tags/" + name) != null) {
      throw new GitError("fatal: tag '" + name + "' already exists");
    }
    String oid = resolve(ctx, target);
    if (oid == null) {
      throw new GitError("fatal: Failed to resolve '" + target
          + "' as a valid ref.");
    }
    if (f.on.contains("-a") || f.vals.containsKey("-m")) {
      String type = Objects.readObject(g, oid).type();
      String msg = Commit.cleanupMessage(f.vals.getOrDefault("-m", ""));
      oid = Objects.writeObject(g, "tag",
          Commit.serializeTag(oid, type, name, ident(ctx), msg));
    }
    // 태그는 reflog 를 남기지 않는다 — logallrefupdates 는 브랜치와
    // HEAD 만 기록한다(git 과 같다)
    String file = Fs.join(g, "refs", "tags", name);
    Fs.mkdirs(Path.of(file).getParent().toString());
    Fs.write(file, (oid + "\n").getBytes(ISO_8859_1));
    return 0;
  }

  // 새것부터 "<7글자> <ref>@{n}: <메시지>" (SPEC.md §6.3).
  static int reflog(Ctx ctx, List<String> args) {
    List<String> rest = parseFlags(args, List.of()).rest.stream()
        .filter(a -> !a.equals("show")).toList();
    String name = rest.isEmpty() ? "HEAD" : rest.get(0);
    String log = Fs.exists(Fs.join(ctx.gitdir(), "logs", name)) ? name
        : Fs.exists(Fs.join(ctx.gitdir(), "logs", HEADS + name))
        ? HEADS + name : null;
    if (log == null) {
      if (name.equals("HEAD")) return 0;
      throw new GitError(AMBIGUOUS.formatted(name));
    }
    List<Refs.Reflog> rows = Refs.readReflog(ctx.gitdir(), log);
    for (int k = 0; k < rows.size(); k++) {
      Refs.Reflog r = rows.get(rows.size() - 1 - k);
      ctx.say(r.next().substring(0, 7) + " " + name + "@{" + k + "}: "
          + r.message() + "\n");
    }
    return 0;
  }

  // ── 6단계: add · rm --cached · status · write-tree · commit ───────

  // 명령줄 경로 → 작업 트리 뿌리에서의 경로 바이트 문자열("" 은 뿌리).
  static String relPath(Ctx ctx, String spec) {
    return Path.of(ctx.root()).relativize(Path.of(ctx.path(spec)))
        .toString();
  }

  static boolean under(String p, String rel) {
    return rel.isEmpty() || p.equals(rel) || p.startsWith(rel + "/");
  }

  static GitError noMatch(String spec) {
    return new GitError("fatal: pathspec '" + spec
        + "' did not match any files");
  }

  // pathspec 아래의 파일을 올리고, 사라진 파일은 뺀다(SPEC.md §9).
  //
  // 모든 pathspec 을 먼저 검사한다 — 하나라도 맞는 것이 없으면 아무것도
  // 바꾸지 않고 멈춘다(git 과 같다).
  static int add(Ctx ctx, List<String> args) {
    String root = ctx.root();
    String g = ctx.gitdir();
    List<Index.IndexEntry> ents = Index.readIndex(g);
    List<String> files = Worktree.walkWorktree(root);
    List<List<String>> hitF = new ArrayList<>();
    List<List<String>> hitI = new ArrayList<>();
    for (String spec : parseFlags(args, List.of()).rest) {
      String rel = relPath(ctx, spec);
      hitF.add(files.stream().filter(f -> under(f, rel)).toList());
      hitI.add(ents.stream().map(e -> e.path).filter(p -> under(p, rel))
          .toList());
      if (hitF.getLast().isEmpty() && hitI.getLast().isEmpty()) {
        throw noMatch(spec);
      }
    }
    Map<String, List<Index.IndexEntry>> byPath = new HashMap<>();
    for (Index.IndexEntry e : ents) {
      byPath.computeIfAbsent(e.path, k -> new ArrayList<>()).add(e);
    }
    for (int k = 0; k < hitF.size(); k++) {
      for (String f : hitF.get(k)) {
        String full = Fs.join(root, f);
        String oid = Objects.writeObject(g, "blob", Fs.read(full));
        byPath.put(f, List.of(Index.entryFromStat(f, full, oid)));
      }
      for (String p : hitI.get(k)) {
        if (!hitF.get(k).contains(p)) byPath.remove(p);
      }
    }
    Index.writeIndex(g, byPath.values().stream()
        .flatMap(List::stream).toList());
    return 0;
  }

  // 찍는 경로는 따옴표 없이 그대로다 — git 의 rm 이 그렇게 찍는다.
  static int rm(Ctx ctx, List<String> args) {
    Flags f = parseFlags(args, List.of("--cached"));
    if (!f.on.contains("--cached")) {
      throw new GitError("fatal: mygit: only rm --cached is supported");
    }
    String g = ctx.gitdir();
    List<Index.IndexEntry> ents = Index.readIndex(g);
    Set<String> have = new HashSet<>();
    ents.forEach(e -> have.add(e.path));
    TreeSet<String> gone = new TreeSet<>();
    for (String spec : f.rest) {
      String rel = relPath(ctx, spec);
      if (!have.contains(rel)) throw noMatch(spec);
      gone.add(rel);
    }
    gone.forEach(p -> ctx.say("rm '" + p + "'\n"));
    Index.writeIndex(g, ents.stream()
        .filter(e -> !gone.contains(e.path)).toList());
    return 0;
  }

  static int status(Ctx ctx, List<String> args) {
    parseFlags(args, List.of("--porcelain", "-s", "--short"));
    Worktree.status(ctx.root(), ctx.gitdir())
        .forEach(row -> ctx.say(row + "\n"));
    return 0;
  }

  // 인덱스(단계 0) → 트리 이름. 충돌 경로가 있으면 쓸 수 없다.
  static String indexTree(Ctx ctx) {
    List<Index.IndexEntry> ents = Index.readIndex(ctx.gitdir());
    if (ents.stream().anyMatch(e -> e.stage != 0)) {
      throw new GitError("error: Committing is not possible because "
          + "you have unmerged files.\nfatal: Exiting because of an "
          + "unresolved conflict.");
    }
    return Tree.writeTree(ctx.gitdir(), ents.stream()
        .map(e -> new Tree.PathEntry(Integer.toOctalString(e.mode),
            e.oid, e.path)).toList());
  }

  static int writeTree(Ctx ctx, List<String> args) {
    parseFlags(args, List.of());
    ctx.say(indexTree(ctx) + "\n");
    return 0;
  }

  // 트리를 쓰고, 커밋하고, 브랜치를 옮긴다(SPEC.md §9 · §6.3).
  //
  // 부모는 HEAD 와, 머지를 마무리하는 중이면 MERGE_HEAD. 출력은 git 의
  // 요약 첫 줄만 — Author 줄과 변경 통계는 줄임이다.
  static int commit(Ctx ctx, List<String> args) {
    List<String> msgs = new ArrayList<>();
    for (int i = 0; i < args.size(); i++) {
      if (!args.get(i).equals("-m")) {
        throw new GitError("fatal: mygit: unknown option '"
            + args.get(i) + "'");
      }
      msgs.add(++i < args.size() ? args.get(i) : "");
    }
    String g = ctx.gitdir();
    Refs.Head h = Refs.readHead(g);
    String mergeHead = Refs.resolveRef(g, "MERGE_HEAD");
    String t = indexTree(ctx);
    if (h.oid() != null && mergeHead == null
        && t.equals(Refs.peel(g, h.oid(), "tree"))) {
      ctx.say("nothing to commit\n");
      return 1;
    }
    String msg = Commit.cleanupMessage(String.join("\n\n", msgs));
    if (msg.isEmpty()) {
      throw new GitError("Aborting commit due to empty commit message.",
          1);
    }
    List<String> parents = new ArrayList<>();
    for (String p : new String[] {h.oid(), mergeHead}) {
      if (p != null) parents.add(p);
    }
    String oid = Objects.writeObject(g, "commit",
        Commit.serializeCommit(t, parents, ident(ctx, "AUTHOR"),
            ident(ctx), msg));
    String subj = Commit.subjectOf(msg);
    String kind = h.oid() == null ? "commit (initial)"
        : mergeHead != null ? "commit (merge)" : "commit";
    Refs.updateRef(g, h.branch() == null ? "HEAD" : h.branch(), oid,
        h.oid(), kind + ": " + subj, ident(ctx));
    for (String f : List.of("MERGE_HEAD", "MERGE_MSG")) {
      Fs.delete(Fs.join(g, f));
    }
    String where = h.branch() == null ? "detached HEAD"
        : h.branch().substring(HEADS.length());
    ctx.say("[" + where + (h.oid() == null ? " (root-commit)" : "")
        + " " + oid.substring(0, 7) + "] " + subj + "\n");
    return 0;
  }

  // ── 7단계: log · merge-base ───────────────────────────────────────

  // 커밋 하나를 git log 의 꼴로(SPEC.md §9.1).
  static String logEntry(Ctx ctx, String oid, boolean oneline) {
    Commit.CommitObj c = Commit.parseCommit(
        Objects.readObject(ctx.gitdir(), oid).body());
    if (oneline) {
      return oid.substring(0, 7) + " " + Commit.subjectOf(c.message())
          + "\n";
    }
    Commit.Ident a = Commit.parseIdent(c.author());
    StringBuilder sb = new StringBuilder("commit " + oid + "\n");
    if (c.parents().size() > 1) {
      sb.append("Merge:");
      c.parents().forEach(p -> sb.append(' ').append(p, 0, 7));
      sb.append('\n');
    }
    sb.append("Author: " + a.name() + " <" + a.mail() + ">\nDate:   "
        + Commit.formatDate(a.secs(), a.tz()) + "\n\n");
    String msg = c.message().endsWith("\n")
        ? c.message().substring(0, c.message().length() - 1)
        : c.message();
    for (String line : msg.split("\n", -1)) {
      sb.append("    ").append(line).append('\n');
    }
    return sb.toString();
  }

  static int log(Ctx ctx, List<String> args) {
    Flags f = parseFlags(args, List.of("--oneline"), "-n");
    String g = ctx.gitdir();
    String start;
    if (!f.rest.isEmpty()) {
      start = resolve(ctx, f.rest.get(0), "commit");
      if (start == null) {
        throw new GitError(AMBIGUOUS.formatted(f.rest.get(0)));
      }
    } else {
      Refs.Head h = Refs.readHead(g);
      start = h.oid();
      if (start == null) {
        throw new GitError("fatal: your current branch '"
            + h.branch().substring(HEADS.length())
            + "' does not have any commits yet");
      }
    }
    List<String> order = Walk.walkLog(g, List.of(start));
    if (f.vals.containsKey("-n")) {
      order = order.subList(0, Math.min(order.size(),
          Integer.parseInt(f.vals.get("-n"))));
    }
    boolean oneline = f.on.contains("--oneline");
    ctx.say(String.join(oneline ? "" : "\n", order.stream()
        .map(oid -> logEntry(ctx, oid, oneline)).toList()));
    return 0;
  }

  static int mergeBase(Ctx ctx, List<String> args) {
    Flags f = parseFlags(args, List.of("--all"));
    if (f.rest.size() != 2) {
      throw new GitError("usage: mygit merge-base [--all] <a> <b>",
          129);
    }
    List<String> ids = new ArrayList<>();
    for (String name : f.rest) {
      String oid = resolve(ctx, name, "commit");
      if (oid == null) {
        throw new GitError("fatal: Not a valid object name " + name);
      }
      ids.add(oid);
    }
    List<String> best = Walk.mergeBases(ctx.gitdir(), ids.get(0),
        ids.get(1));
    if (best.isEmpty()) return 1;
    for (String oid : f.on.contains("--all") ? best
        : best.subList(0, 1)) {
      ctx.say(oid + "\n");
    }
    return 0;
  }

  // ── 8단계: diff ───────────────────────────────────────────────────

  // 디스크의 파일 한쪽. 없으면 null.
  static Diff.Side diskSide(String path) {
    Worktree.Stat st = Worktree.fileState(path, "");
    return st == null ? null
        : new Diff.Side(st.mode(), st.oid(), Fs.read(path));
  }

  // <rev> 의 트리를 펼쳐 {경로: (모드, 이름)}.
  static Map<String, Worktree.Stat> revTree(Ctx ctx, String rev) {
    String t = resolve(ctx, rev, "tree");
    if (t == null) throw new GitError(AMBIGUOUS.formatted(rev));
    return Worktree.treeMap(ctx.gitdir(), t);
  }

  // SPEC.md §11.5 의 네 꼴. --no-index 만 다르면 1 로 끝난다.
  static int diff(Ctx ctx, List<String> args) {
    Flags f = parseFlags(args, List.of("--cached", "--no-index"));
    if (f.on.contains("--no-index")) {
      if (f.rest.size() != 2) {
        throw new GitError("usage: mygit diff --no-index <a> <b>", 129);
      }
      String text = Diff.fileDiff(f.rest.get(0), f.rest.get(1),
          diskSide(ctx.path(f.rest.get(0))),
          diskSide(ctx.path(f.rest.get(1))));
      ctx.say(text);
      return text.isEmpty() ? 0 : 1;
    }
    String g = ctx.gitdir();
    boolean worktree = f.rest.isEmpty() && !f.on.contains("--cached");
    Map<String, Worktree.Stat> a;
    Map<String, Worktree.Stat> b = new TreeMap<>();
    if (f.rest.size() == 2) {
      a = revTree(ctx, f.rest.get(0));
      b = revTree(ctx, f.rest.get(1));
    } else if (f.rest.isEmpty()) {
      // 인덱스(단계 0)가 한쪽 — --cached 면 새 쪽, 아니면 옛 쪽
      List<Index.IndexEntry> ents = Index.readIndex(g);
      Set<String> unmerged = new HashSet<>();
      ents.stream().filter(e -> e.stage != 0)
          .forEach(e -> unmerged.add(e.path));
      for (Index.IndexEntry e : ents) {
        if (!unmerged.contains(e.path)) {     // 충돌 경로는 건너뛴다
          b.put(e.path, new Worktree.Stat(e.mode, e.oid));
        }
      }
      if (worktree) {
        a = b;
        b = new TreeMap<>();
        for (String p : a.keySet()) {
          Worktree.Stat st = Worktree.fileState(ctx.root(), p);
          if (st != null) b.put(p, st);
        }
      } else {
        String head = Refs.readHead(g).oid();
        a = head == null ? Map.of() : revTree(ctx, head);
      }
    } else {
      throw new GitError(AMBIGUOUS.formatted(f.rest.get(0)));
    }
    TreeSet<String> paths = new TreeSet<>(a.keySet());
    paths.addAll(b.keySet());
    for (String p : paths) {
      Worktree.Stat o = a.get(p);
      Worktree.Stat n = b.get(p);
      if (java.util.Objects.equals(o, n)) continue;
      ctx.say(Diff.fileDiff(p, p,
          o == null ? null : Diff.blobSide(g, o.mode(), o.oid()),
          n == null ? null : worktree ? diskSide(Fs.join(ctx.root(), p))
              : Diff.blobSide(g, n.mode(), n.oid())));
    }
    return 0;
  }

  // ── 9단계: switch · checkout ──────────────────────────────────────

  // "<7글자> <제목>" — HEAD is now at … 의 꼬리.
  static String summaryLine(Ctx ctx, String oid) {
    return oid.substring(0, 7) + " " + Commit.subjectOf(Commit
        .parseCommit(Objects.readObject(ctx.gitdir(), oid).body())
        .message());
  }

  // 작업 트리를 oid 로 옮기고 HEAD 를 branch(null 이면 분리)로
  // (SPEC.md §9.3).
  //
  // 안내는 표준 오류에, 남은 변경 알림은 표준 출력에. reflog 는
  // "checkout: moving from <옛> to <arg 그대로>" — 옛 쪽이 분리
  // 상태면 40글자다(§6.3). fresh 는 switch -c 로 막 만든 브랜치 —
  // 지금 커밋에서 만들었으면 git 이 작업 트리를 건드리지 않고 남은
  // 변경도 알리지 않는다(golden/scen/checkout.scn).
  static int moveHead(Ctx ctx, String branch, String oid, String arg,
      boolean fresh) {
    String g = ctx.gitdir();
    Refs.Head old = Refs.readHead(g);
    String oldTree = old.oid() == null ? null
        : Refs.peel(g, old.oid(), "tree");
    String newTree = Refs.peel(g, oid, "tree");
    Worktree.checkoutTree(ctx.root(), g, oldTree, newTree);
    // 분리 상태를 떠나되 커밋이 바뀔 때만 — 같은 커밋이면 git 도
    // 찍지 않는다
    if (old.branch() == null && old.oid() != null
        && !oid.equals(old.oid())) {
      ctx.warn("Previous HEAD position was "
          + summaryLine(ctx, old.oid()) + "\n");
    }
    Refs.setHead(g, branch == null ? oid : branch);
    String from = old.branch() == null ? old.oid()
        : old.branch().substring(HEADS.length());
    Refs.appendReflog(g, "HEAD", old.oid(), oid, ident(ctx),
        "checkout: moving from " + from + " to " + arg);
    if (!fresh || !oid.equals(old.oid())) {
      Worktree.localChanges(ctx.root(), g, newTree)
          .forEach(row -> ctx.say(row + "\n"));
    }
    ctx.warn(branch == null
        ? "HEAD is now at " + summaryLine(ctx, oid) + "\n"
        : fresh ? "Switched to a new branch '" + arg + "'\n"
        : branch.equals(old.branch()) ? "Already on '" + arg + "'\n"
        : "Switched to branch '" + arg + "'\n");
    return 0;
  }

  static int createAndSwitch(Ctx ctx, String name, String start) {
    String g = ctx.gitdir();
    if (!Refs.validBranchName(name)) {
      throw new GitError("fatal: '" + name
          + "' is not a valid branch name");
    }
    if (Refs.resolveRef(g, HEADS + name) != null) {
      throw new GitError("fatal: a branch named '" + name
          + "' already exists");
    }
    if (Refs.readHead(g).oid() == null && start == null) {
      // 첫 커밋 전 — HEAD 가 가리키는 이름만 바꾼다
      Refs.setHead(g, HEADS + name);
      ctx.warn("Switched to a new branch '" + name + "'\n");
      return 0;
    }
    String arg = start == null ? "HEAD" : start;
    String oid = resolve(ctx, arg, "commit");
    if (oid == null) {
      throw new GitError("fatal: invalid reference: " + arg);
    }
    Refs.updateRef(g, HEADS + name, oid, null,
        "branch: Created from " + arg, ident(ctx));
    return moveHead(ctx, HEADS + name, oid, name, true);
  }

  static int switchTo(Ctx ctx, List<String> args) {
    Flags f = parseFlags(args, List.of(), "-c");
    if (f.vals.containsKey("-c")) {
      return createAndSwitch(ctx, f.vals.get("-c"),
          f.rest.isEmpty() ? null : f.rest.get(0));
    }
    if (f.rest.size() != 1) {
      throw new GitError("usage: mygit switch [-c] <branch>", 129);
    }
    String name = f.rest.get(0);
    String oid = Refs.resolveRef(ctx.gitdir(), HEADS + name);
    if (oid != null) {
      return moveHead(ctx, HEADS + name, oid, name, false);
    }
    if (resolve(ctx, name) != null) {
      throw new GitError("fatal: a branch is expected, got commit '"
          + name + "'");
    }
    throw new GitError("fatal: invalid reference: " + name);
  }

  static int checkout(Ctx ctx, List<String> args) {
    List<String> rest = parseFlags(args, List.of()).rest;
    if (rest.size() != 1) {
      throw new GitError("usage: mygit checkout <branch|commit>", 129);
    }
    String name = rest.get(0);
    String oid = Refs.resolveRef(ctx.gitdir(), HEADS + name);
    if (oid != null) {
      return moveHead(ctx, HEADS + name, oid, name, false);
    }
    oid = resolve(ctx, name, "commit");
    if (oid == null) {
      throw new GitError("error: pathspec '" + name
          + "' did not match any file(s) known to git", 1);
    }
    return moveHead(ctx, null, oid, name, false);
  }

  // ── 틀 ────────────────────────────────────────────────────────────
  // 명령 이름 → 함수. 단계가 늘 때마다 한 줄씩 는다.
  private static Command command(String name) {
    return switch (name) {
      case "hash-object" -> Cli::hashObject;
      case "cat-file" -> Cli::catFile;
      case "init" -> Cli::init;
      case "commit-tree" -> Cli::commitTree;
      case "branch" -> Cli::branch;
      case "tag" -> Cli::tag;
      case "reflog" -> Cli::reflog;
      case "add" -> Cli::add;
      case "rm" -> Cli::rm;
      case "status" -> Cli::status;
      case "write-tree" -> Cli::writeTree;
      case "commit" -> Cli::commit;
      case "log" -> Cli::log;
      case "merge-base" -> Cli::mergeBase;
      case "diff" -> Cli::diff;
      case "switch" -> Cli::switchTo;
      case "checkout" -> Cli::checkout;
      default -> null;
    };
  }

  // 명령 하나를 돌린다 → (종료 코드, 표준 출력, 표준 오류). stdin 이
  // null 이면 진짜 표준 입력을 (필요할 때만) 읽는다. 인자와 환경은
  // 유니코드로 받는다.
  public static Result run(List<String> args, String cwd,
      Map<String, String> env, byte[] stdin) {
    Ctx ctx = new Ctx(cwd, env, stdin);
    List<String> a = args.stream().map(Cli::bytes).toList();
    int code;
    try {
      if (a.isEmpty()) {
        throw new GitError("usage: mygit <command> [<args>]", 129);
      }
      Command fn = command(a.get(0));
      if (fn == null) {
        throw new GitError("mygit: '" + a.get(0)
            + "' is not a mygit command.", 1);
      }
      code = fn.run(ctx, a.subList(1, a.size()));
    } catch (GitError e) {
      ctx.warn(e.getMessage() + "\n");
      code = e.code;
    } catch (UncheckedIOException e) {
      ctx.warn("fatal: mygit: " + e.getCause().getMessage() + "\n");
      code = 128;
    }
    return new Result(code, ctx.out.toByteArray(),
        ctx.err.toByteArray());
  }
}
