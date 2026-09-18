package mygit.tests;

import static java.nio.charset.StandardCharsets.UTF_8;
import static mygit.tests.Check.eq;
import static mygit.tests.Check.gitError;

import java.time.Instant;
import java.time.ZoneOffset;
import java.time.format.DateTimeFormatter;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import mygit.Cli;
import mygit.Commit;
import mygit.Fs;
import mygit.Objects;
import mygit.Refs;

// commit·tag·신원 줄과 참조의 시험 — SPEC.md §4.4 · §4.5 · §6, 5단계.
//
// 가장 강한 오라클은 "같은 입력에서 같은 이름" 이다. golden/objects 의
// 커밋(b23b7a5…)과 태그(5702a43…)는 tools/gitenv.sh 의 고정 환경에서
// 진짜 git 이 만들었다 — mygit 이 같은 트리·같은 환경으로 만든 커밋과
// 태그는 바이트까지 같아야 하고, 그러면 이름도 같다.
final class CommitTest {
  static final String COMMIT =
      "b23b7a5fefc32902eb83feac2800cf158140dcb1";
  static final String TAG = "5702a431dba432bfe47c3b3fdda3835a8f542f5c";
  static final String CO = "C O Mitter <committer@example.com> "
      + "1700000000 +0900";

  private CommitTest() {}

  static void s4_4_parseIdent() {
    eq(new Commit.Ident("A U Thor", "author@example.com", 1700000000L,
        "+0900"), Commit.parseIdent(
            "A U Thor <author@example.com> 1700000000 +0900"));
  }

  static void s9_1_dateMatchesGitLog() {
    // golden/scen/hello.scn: git log 이 찍은 두 날짜
    eq("Wed Nov 15 07:13:20 2023 +0900",
        Commit.formatDate(1700000000L, "+0900"));
    eq("Wed Nov 15 07:14:20 2023 +0900",
        Commit.formatDate(1700000060L, "+0900"));
  }

  static void s9_1_dateOtherZonesAgreeWithJavaTime() {
    // 달력 계산은 손으로 한다 — java.time 은 증인으로만
    var fmt = DateTimeFormatter.ofPattern("EEE MMM d HH:mm:ss yyyy",
        Locale.ENGLISH);
    for (long secs : new long[] {0, 86399, 951782400, 1700000000,
        2000000000, 1709251199, 4102444800L}) {
      for (String tz : List.of("+0000", "-0700", "+0530", "-1200",
          "+1400")) {
        var off = ZoneOffset.of(tz.substring(0, 3) + ":"
            + tz.substring(3));
        String want = Instant.ofEpochSecond(secs).atOffset(off)
            .format(fmt) + " " + tz;
        eq(want, Commit.formatDate(secs, tz), secs, tz);
      }
    }
  }

  static void s1_3_missingEnvIsAnError() throws Exception {
    Map<String, String> env = new HashMap<>(Sandbox.IDENT);
    env.remove("GIT_AUTHOR_DATE");
    eq("fatal: mygit: GIT_AUTHOR_DATE is not set", gitError(
        () -> Commit.identFromEnv(env, "AUTHOR")).getMessage());
    env.put("GIT_AUTHOR_DATE", "yesterday");
    eq("fatal: mygit: GIT_AUTHOR_DATE is not '<seconds> <+hhmm>'",
        gitError(() -> Commit.identFromEnv(env, "AUTHOR"))
            .getMessage());
  }

  static void s4_4_cleanupMatchesGit() {
    // SPEC.md §4.4 의 예 — 진짜 git commit -m 으로 확인한 것
    eq("  lead\n\nx\n\ny\n", Commit.cleanupMessage(
        "\n\n  lead  \n\nx   \n \n\n\ny\n\n"));
    eq("one\n", Commit.cleanupMessage("one"));
    eq("", Commit.cleanupMessage(" \n \n"));
  }

  static void s4_4_subjectJoinsTheFirstParagraph() {
    eq("second", Commit.subjectOf("second\n\nbody line\n"));
    eq("second body line",
        Commit.subjectOf("second\nbody line\n\npara2\n"));
  }

  static void s4_4_parseAndRebuildGitCommit() throws Exception {
    byte[] body = BlobTest.bodyOf(COMMIT);
    var c = Commit.parseCommit(body);
    eq(List.of(), c.parents());
    eq(body, Commit.serializeCommit(c.tree(), c.parents(), c.author(),
        c.committer(), c.message()));
  }

  static void s4_5_tagBytesMatchGit() throws Exception {
    eq(BlobTest.bodyOf(TAG), Commit.serializeTag(COMMIT, "commit", "v1",
        CO, "tag message\n"));
  }

  // mygit init 으로 만든 저장소 + golden 객체 전부
  static Sandbox repo() throws Exception {
    Sandbox sb = new Sandbox(false);
    sb.mygit("init");
    for (var row : ObjectsTest.objs()) sb.plant(row.get("id"));
    return sb;
  }

  static String treeOfCommit() throws Exception {
    return Commit.parseCommit(BlobTest.bodyOf(COMMIT)).tree();
  }

  static String read(Sandbox sb, String name) {
    return new String(Fs.read(Fs.join(sb.gitdir, name)), UTF_8);
  }

  static void s5_1_layoutAndMessage() throws Exception {
    try (var sb = new Sandbox(false)) {
      Cli.Result r = sb.mygit("init");
      eq(0, r.code());
      eq(0, r.err().length);
      eq("Initialized empty Git repository in " + sb.root + "/.git/\n",
          new String(r.out(), UTF_8));
      eq("ref: refs/heads/main\n", read(sb, "HEAD"));
      eq("[core]\n\trepositoryformatversion = 0\n\tfilemode = true\n"
          + "\tbare = false\n\tlogallrefupdates = true\n",
          read(sb, "config"));
      for (String d : List.of("objects/pack", "refs/heads",
          "refs/tags")) {
        eq(true, Fs.isDir(Fs.join(sb.gitdir, d)), d);
      }
    }
  }

  static void s5_1_reinitTouchesNothing() throws Exception {
    try (var sb = new Sandbox(false)) {
      sb.mygit("init");
      Fs.write(Fs.join(sb.gitdir, "HEAD"),
          "ref: refs/heads/dev\n".getBytes());
      eq("Reinitialized existing Git repository in " + sb.root
          + "/.git/\n", sb.out("init"));
      eq("ref: refs/heads/dev\n", read(sb, "HEAD"));
    }
  }

  static void s5_1_initIntoANewDirectory() throws Exception {
    try (var sb = new Sandbox(false)) {
      eq(0, sb.mygit("init", "sub").code());
      eq(true, Fs.isDir(Fs.join(sb.root, "sub", ".git")));
    }
  }

  static void s4_4_commitTreeReproducesGitCommit() throws Exception {
    try (var sb = repo()) {
      Cli.Result r = sb.mygit("commit-tree", treeOfCommit(), "-m",
          "objects");
      eq(0, r.code());
      eq(COMMIT + "\n", new String(r.out(), UTF_8));
      eq(0, r.err().length);
    }
  }

  static void s4_4_parentsAndMessages() throws Exception {
    try (var sb = repo()) {
      String t = treeOfCommit();
      String oid = sb.out("commit-tree", t, "-p", COMMIT, "-m", "a",
          "-m", "b").strip();
      var c = Commit.parseCommit(Objects.readObject(sb.gitdir, oid)
          .body());
      eq(List.of(COMMIT), c.parents());
      eq("a\n\nb\n", c.message());
      oid = sb.out("commit-tree", t, "-m", "  m1  ").strip();
      eq("  m1  \n", Commit.parseCommit(Objects.readObject(sb.gitdir,
          oid).body()).message());
    }
  }

  static void s4_5_annotatedTagReproducesGitTag() throws Exception {
    try (var sb = repo()) {
      sb.mygit("branch", "main", COMMIT);
      Cli.Result r = sb.mygit("tag", "-a", "v1", "-m", "tag message");
      eq(0, r.code());
      eq(0, r.out().length + r.err().length);
      eq(TAG, Refs.resolveRef(sb.gitdir, "refs/tags/v1"));
    }
  }

  static void s1_4_errors() throws Exception {
    var errors = BlobTest.errors();
    try (var sb = repo()) {
      sb.mygit("branch", "main", COMMIT);
      for (String cmd : List.of("commit-tree nope -m x",
          "branch x nope", "tag t nope", "branch main",
          "branch a..b")) {
        eq(errors.get(cmd), Sandbox.firstLine(sb.mygit(cmd.split(" "))),
            cmd);
      }
      sb.mygit("tag", "t");
      eq(errors.get("tag t"), Sandbox.firstLine(sb.mygit("tag", "t")));
    }
  }

  static void s9_2_listAndCreate() throws Exception {
    try (var sb = repo()) {
      eq(0, sb.mygit("branch", "main", COMMIT).code());
      sb.mygit("branch", "topic");
      eq("* main\n  topic\n", sb.out("branch"));
      eq(COMMIT, Refs.resolveRef(sb.gitdir, "refs/heads/topic"));
    }
  }

  static void s6_3_branchReflog() throws Exception {
    try (var sb = repo()) {
      sb.mygit("branch", "main", COMMIT);
      sb.mygit("branch", "topic", "main");
      eq(List.of(new Refs.Reflog(Refs.ZERO, COMMIT, CO,
          "branch: Created from main")),
          Refs.readReflog(sb.gitdir, "refs/heads/topic"));
      eq(COMMIT.substring(0, 7)
          + " topic@{0}: branch: Created from main\n",
          sb.out("reflog", "topic"));
    }
  }

  static void s6_3_reflogLineBytes() throws Exception {
    try (var sb = new Sandbox(false)) {
      sb.mygit("init");
      Refs.appendReflog(sb.gitdir, "HEAD", Refs.ZERO, COMMIT,
          "X <x@y> 1 +0000", "commit (initial): t");
      eq(Refs.ZERO + " " + COMMIT
          + " X <x@y> 1 +0000\tcommit (initial): t\n",
          read(sb, "logs/HEAD"));
    }
  }

  // golden/dag/equal — 진짜 git 이 만든 역사를 임시 .git 으로 옮기고
  // body 를 돈다. ids 는 그 저장소에서 git log --oneline 이 찍은 것
  // (expect.txt): "<차례>:<제목>" → 7글자.
  interface InDag {
    void run(String gitdir, Map<String, String> ids) throws Exception;
  }

  static void withDag(String name, InDag body) throws Exception {
    try (var sb = Sandbox.dag(name)) {
      String text = new String(Golden.read("dag", name, "expect.txt"),
          UTF_8);
      String block = text.split("\\$ git log --oneline\n")[1]
          .split("= 0")[0].strip();
      Map<String, String> ids = new HashMap<>();
      String[] lines = block.split("\n");
      for (int k = 0; k < lines.length; k++) {
        String[] ab = lines[k].split(" ", 2);
        ids.put(k + ":" + ab[1], ab[0]);
      }
      body.run(sb.gitdir, ids);
    }
  }

  static void s6_2_namesAndSuffixes() throws Exception {
    withDag("equal", (g, i) -> {
      Map<String, String> rp = new HashMap<>();
      for (String spec : List.of("HEAD", "main", "refs/heads/main",
          "main~1", "HEAD~2", "HEAD~1^2", "HEAD^^", "t", "HEAD^0",
          i.get("2:G"), "nope", "HEAD~99")) {
        String oid = Refs.revParse(g, spec);
        rp.put(spec, oid == null ? null : oid.substring(0, 7));
      }
      eq(i.get("0:I"), rp.get("HEAD"));
      eq(i.get("0:I"), rp.get("main"));
      eq(i.get("0:I"), rp.get("refs/heads/main"));
      eq(i.get("1:Merge branch 't'"), rp.get("main~1"));
      eq(i.get("2:G"), rp.get("HEAD~2"));          // 첫 부모
      eq(i.get("3:H"), rp.get("HEAD~1^2"));        // 둘째 부모
      eq(i.get("2:G"), rp.get("HEAD^^"));
      eq(i.get("3:H"), rp.get("t"));
      eq(i.get("2:G"), rp.get(i.get("2:G")));      // 앞부분
      eq(i.get("0:I"), rp.get("HEAD^0"));
      eq(null, rp.get("nope"));
      eq(null, rp.get("HEAD~99"));
    });
  }

  static void s6_2_treeSuffix() throws Exception {
    withDag("equal", (g, i) -> eq("tree", Objects.readObject(g,
        Refs.revParse(g, "HEAD^{tree}")).type()));
  }
}
