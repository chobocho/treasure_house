package mygit.tests;

import static java.nio.charset.StandardCharsets.UTF_8;
import static mygit.tests.Check.eq;
import static mygit.tests.Check.ok;

import java.util.List;
import mygit.Cli;
import mygit.Refs;
import mygit.Walk;

// 역사 걷기·merge-base·branch -d 의 시험 — SPEC.md §9.1 · §9.2 · §10,
// 7단계 "log · DAG 순회 · merge-base".
//
// golden/dag/<역사>/git 은 진짜 git 이 만든 .git 이고, expect.txt 는
// 그 저장소에서 git 이 찍은 log·merge-base 출력이다. equal 은 모든
// 커밋의 날짜가 같아(§10.1 의 "먼저 온 것이 먼저" 규칙이 차례를 전부
// 정한다), dated 는 날짜가 모두 다르고, criss 는 가장 좋은 공통
// 조상이 둘이다.
// criss-equal 은 criss 와 같되 날짜가 모두 같아, 두 공통 조상의
// 차례를 인자 순서와 부모 순서가 정한다(SPEC.md §10.2).
final class WalkTest {
  private WalkTest() {}

  static void s10_logAndMergeBaseMatchGit() throws Exception {
    int n = 0;
    for (String name :
         List.of("equal", "dated", "criss", "criss-equal")) {
      try (var sb = Sandbox.dag(name)) {
        String text = new String(Golden.read("dag", name, "expect.txt"),
            UTF_8);
        String[] blocks = text.split("\\$ git ");
        for (String block : List.of(blocks).subList(1, blocks.length)) {
          // 명령 줄 · 기대 표준 출력 · "= 코드"
          int nl = block.indexOf('\n');
          int eqAt = block.lastIndexOf("= ");
          Cli.Result r = sb.mygit(block.substring(0, nl).split(" "));
          String where = name + ": " + block.substring(0, nl);
          eq(Integer.parseInt(block.substring(eqAt + 2).strip()),
              r.code(), where);
          eq(block.substring(nl + 1, eqAt), new String(r.out(), UTF_8),
              where);
          n++;
        }
      }
    }
    ok(n >= 14, n);
  }

  static void s10_1_equalDatesFirstInFirstOut() throws Exception {
    // SPEC.md §10.1 의 예: I M2 G H M1 F D E C B A
    try (var sb = Sandbox.dag("equal")) {
      String head = Refs.revParse(sb.gitdir, "HEAD");
      List<String> order = Walk.walkLog(sb.gitdir, List.of(head));
      eq(11, order.size());
      eq(head, order.get(0));
    }
  }

  static void s10_2_isAncestor() throws Exception {
    try (var sb = Sandbox.dag("equal")) {
      String head = Refs.revParse(sb.gitdir, "HEAD");
      String t = Refs.revParse(sb.gitdir, "t");
      eq(true, Walk.isAncestor(sb.gitdir, t, head));
      eq(false, Walk.isAncestor(sb.gitdir, head, t));
      eq(true, Walk.isAncestor(sb.gitdir, head, head));
    }
  }

  static void s9_2_deleteMergedBranch() throws Exception {
    try (var sb = Sandbox.dag("equal")) {
      String t = Refs.revParse(sb.gitdir, "t");
      Cli.Result r = sb.mygit("branch", "-d", "t");
      eq(0, r.code());
      eq("Deleted branch t (was " + t.substring(0, 7) + ").\n",
          new String(r.out(), UTF_8));
      eq(0, r.err().length);
      eq(null, Refs.resolveRef(sb.gitdir, "refs/heads/t"));
    }
  }

  static void s9_2_refusesUnmergedBranch() throws Exception {
    try (var sb = Sandbox.dag("equal")) {
      sb.mygit("branch", "old", "HEAD~1");
      // HEAD 를 뒤로 돌려 old 가 HEAD 에서 닿지 않게 한다
      Refs.setHead(sb.gitdir, Refs.revParse(sb.gitdir, "HEAD~2"));
      Cli.Result r = sb.mygit("branch", "-d", "old");
      eq(1, r.code());
      eq("error: the branch 'old' is not fully merged\n",
          new String(r.err(), UTF_8));
    }
  }

  static void s9_2_refusesCurrentBranch() throws Exception {
    try (var sb = Sandbox.dag("equal")) {
      Cli.Result r = sb.mygit("branch", "-d", "main");
      eq(1, r.code());
      eq("error: cannot delete branch 'main' used by worktree at '"
          + sb.root + "'\n", new String(r.err(), UTF_8));
    }
  }

  static void s1_4_unknownRevision() throws Exception {
    try (var sb = Sandbox.dag("equal")) {
      eq("128 fatal: ambiguous argument 'nope': unknown revision or "
          + "path not in the working tree.",
          Sandbox.firstLine(sb.mygit("log", "nope")));
    }
  }

  static void s9_1_limit() throws Exception {
    try (var sb = Sandbox.dag("equal")) {
      eq(4, sb.out("log", "--oneline", "-n", "3").split("\n", -1)
          .length);
    }
  }
}
