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
  static final class Ctx {
    final String cwd;
    final Map<String, String> env = new HashMap<>();
    final ByteArrayOutputStream out = new ByteArrayOutputStream();
    final ByteArrayOutputStream err = new ByteArrayOutputStream();
    private byte[] stdin;
    private String top;

    Ctx(String cwd, Map<String, String> env, byte[] stdin) {
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

    String gitdir() {
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
    Flags f = parseFlags(args, List.of());
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

  // ── 틀 ────────────────────────────────────────────────────────────
  private static final Map<String, Command> COMMANDS = Map.of(
      "hash-object", Cli::hashObject,
      "cat-file", Cli::catFile,
      "init", Cli::init,
      "commit-tree", Cli::commitTree,
      "branch", Cli::branch,
      "tag", Cli::tag,
      "reflog", Cli::reflog);

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
      Command fn = COMMANDS.get(a.get(0));
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
