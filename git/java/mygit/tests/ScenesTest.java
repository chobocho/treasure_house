package mygit.tests;

import static java.nio.charset.StandardCharsets.ISO_8859_1;
import static java.nio.charset.StandardCharsets.UTF_8;
import static mygit.tests.Check.eq;

import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.nio.file.attribute.PosixFilePermissions;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import mygit.Cli;
import mygit.Fs;
import mygit.Index;
import mygit.Main;
import mygit.Refs;
import mygit.Worktree;

// 장면 시험 — golden/scen/*.scn 을 mygit 으로 다시 돌린다
// (SPEC.md §16.4).
//
// 장면의 기대 출력은 진짜 git 2.55.0 이 채웠다. 이 실행기는 같은
// 명령을 빈 임시 디렉터리에서 mygit 으로 돌리고, 명령마다 표준 출력·
// 표준 오류·종료 코드를 한 글자씩 견준다. 장면은 자기에게 필요한
// 명령이 다 생기는 단계(STEP)부터 켜진다 — 그 전에는 이유를 달고
// 건너뛴다. 12단계를 마치면 건너뛰는 장면이 하나도 없어야 한다.
final class ScenesTest {
  // 장면 → 켜지는 단계 (그 장면이 쓰는 명령이 모두 생기는 단계)
  static final Map<String, Integer> NEEDS = Map.of("plumbing", 6,
      "status", 6, "hello", 7, "diff", 8, "checkout", 9, "errors", 10,
      "clone", 12);

  private ScenesTest() {}

  static int stepOf(String name) {
    return name.startsWith("merge-") ? 10 : NEEDS.get(name);
  }

  // SPEC.md §16.4 — 공백으로 가르고 "…" 는 한 덩어리.
  static List<String> splitArgs(String line) {
    List<String> args = new ArrayList<>();
    StringBuilder cur = null;
    boolean quoted = false;
    for (int i = 0; i < line.length(); i++) {
      char c = line.charAt(i);
      if (quoted) {
        if (c == '\\' && i + 1 < line.length()) {
          char n = line.charAt(++i);
          cur.append(n == 'n' ? '\n' : n == 't' ? '\t' : n);
        } else if (c == '"') {
          quoted = false;
        } else {
          cur.append(c);
        }
      } else if (c == '"') {
        quoted = true;
        if (cur == null) cur = new StringBuilder();
      } else if (Character.isWhitespace(c)) {
        if (cur != null) args.add(cur.toString());
        cur = null;
      } else {
        if (cur == null) cur = new StringBuilder();
        cur.append(c);
      }
    }
    if (cur != null) args.add(cur.toString());
    return args;
  }

  record Step(String line, List<String> want) {}

  // .scn → 명령 줄과 기대 줄들. 기대 줄은 "> " · "! " · "= " 로
  // 시작하거나 "%noeol" 이다.
  static List<Step> parse(String text) {
    List<Step> steps = new ArrayList<>();
    for (String line : text.split("\n")) {
      if (line.isEmpty() || line.startsWith("#")) continue;
      if (line.matches("[>!=] .*") || line.equals("%noeol")) {
        steps.get(steps.size() - 1).want.add(line);
      } else {
        steps.add(new Step(line, new ArrayList<>()));
      }
    }
    return steps;
  }

  // 실제 결과를 .scn 의 기대 줄 꼴로 — 같은 규칙으로 견주려고.
  static List<String> render(Cli.Result r) {
    List<String> rows = new ArrayList<>();
    String[] prefixes = {"> ", "! "};
    byte[][] datas = {r.out(), r.err()};
    for (int k = 0; k < 2; k++) {
      String text = new String(datas[k], UTF_8);
      if (text.isEmpty()) continue;
      boolean eol = text.endsWith("\n");
      String body = eol ? text.substring(0, text.length() - 1) : text;
      for (String l : body.split("\n", -1)) rows.add(prefixes[k] + l);
      if (!eol) rows.add("%noeol");
    }
    if (r.code() != 0) rows.add("= " + r.code());
    return rows;
  }

  static final class Scene {
    final String root;
    String cwd;
    final Map<String, String> env = new HashMap<>(System.getenv());

    Scene(String root) {
      this.root = root;
      cwd = root;
      env.putAll(Sandbox.IDENT);
      env.put("GIT_CEILING_DIRECTORIES",
          Path.of(root).getParent().toString());
    }

    void date(String secs) {
      env.put("GIT_AUTHOR_DATE", secs + " +0900");
      env.put("GIT_COMMITTER_DATE", secs + " +0900");
    }

    String gitdir() {
      return new Cli.Ctx(cwd, env, new byte[0]).gitdir();
    }

    static Cli.Result text(String s) {
      return new Cli.Result(0, s.getBytes(ISO_8859_1), new byte[0]);
    }

    // 한 줄을 돌려 결과를. 손질 줄은 null.
    Cli.Result run(String line) throws Exception {
      List<String> a = splitArgs(line);
      Path p = a.size() > 1 ? Path.of(cwd, Golden.b(a.get(1))) : null;
      switch (a.get(0)) {
        case "@date" -> date(a.get(1));
        case "@cd" -> cwd = Path.of(root, a.get(1)).normalize()
            .toString();
        case "write", "append" -> {
          Files.createDirectories(p.getParent());
          Files.write(p, Golden.make(a.get(2)),
              StandardOpenOption.CREATE, a.get(0).equals("append")
                  ? StandardOpenOption.APPEND
                  : StandardOpenOption.TRUNCATE_EXISTING);
        }
        case "chmod" -> Files.setPosixFilePermissions(p,
            PosixFilePermissions.fromString(a.get(2).equals("755")
                ? "rwxr-xr-x" : "rw-r--r--"));
        case "rm" -> Files.delete(p);
        case "mkdir" -> Files.createDirectories(p);
        case "mygit" -> {
          return Cli.run(a.subList(1, a.size()).stream()
              .map(x -> x.replace("<ROOT>", root)).toList(), cwd, env,
              new byte[0]);
        }
        case "cat" -> {
          return new Cli.Result(0, Files.readAllBytes(p), new byte[0]);
        }
        case "stage" -> {
          StringBuilder sb = new StringBuilder();
          for (var e : Index.readIndex(gitdir())) {
            sb.append(String.format("%06o %s %d\t%s\n", e.mode, e.oid,
                e.stage, Worktree.quotePath(e.path)));
          }
          return text(sb.toString());
        }
        case "ref" -> {
          return text(Refs.revParse(gitdir(), Golden.b(a.get(1)))
              + "\n");
        }
        default -> throw new IllegalArgumentException(
            "모르는 장면 줄: " + line);
      }
      return null;
    }
  }

  static void scene(String name) throws Exception {
    if (Main.STEP < stepOf(name)) {
      Check.skip(stepOf(name) + "단계에서 켜진다");
    }
    String tmp = Golden.tempdir();
    try {
      String root = Fs.join(tmp, "scene");
      Fs.mkdirs(root);
      Scene sc = new Scene(root);
      sc.date("1700000000");
      List<Step> steps = parse(new String(Golden.read("scen",
          name + ".scn"), UTF_8));
      for (int k = 0; k < steps.size(); k++) {
        Step st = steps.get(k);
        Cli.Result got = sc.run(st.line);
        List<String> want = st.want.stream()
            .map(w -> w.replace("<ROOT>", root)).toList();
        eq(want, got == null ? List.of() : render(got),
            name + " 장면 " + k + "번째 줄: " + st.line);
      }
    } finally {
      Golden.rmTree(tmp);
    }
  }

  // 장면마다 시험 하나 — 이름은 s16_4_<장면>
  static void all() {
    for (String f : Fs.list(Golden.path("scen"))) {
      String name = f.substring(0, f.length() - 4);
      Check.test("ScenesTest.s16_4_" + name, () -> scene(name));
    }
  }
}
