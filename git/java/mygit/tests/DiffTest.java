package mygit.tests;

import static java.nio.charset.StandardCharsets.ISO_8859_1;
import static mygit.tests.Check.eq;
import static mygit.tests.Check.ok;

import java.util.Arrays;
import java.util.List;
import mygit.Cli;
import mygit.Diff;

// diff 의 시험 — SPEC.md §11, 8단계 "diff — Myers 알고리즘".
//
// golden/diff/ 는 진짜 `git -c diff.indentHeuristic=false diff
// --no-index` 의 출력이다. agree 30쌍은 바이트까지 같아야 하고, tie
// 3쌍은 git 이 같은 길이의 **다른** 편집 스크립트를 고르는 쌍이다 —
// 거기서는 지운 줄·끼운 줄의 수가 같고 출력은 달라야 한다(SPEC.md
// §11.2). 세 영역 사이의 diff 는 golden/scen/diff.scn 이 장면 시험으로
// 본다. Python 만 가진 선형 공간 변형(결정 7)의 시험은 여기 없다.
final class DiffTest {
  private DiffTest() {}

  static Cli.Result runPair(Sandbox sb, String stem) throws Exception {
    for (String ext : List.of(".a", ".b")) {
      sb.put(stem + ext, Golden.read("diff", stem + ext));
    }
    return sb.mygit("diff", "--no-index", stem + ".a", stem + ".b");
  }

  static void s11_agreePairsAreByteIdentical() throws Exception {
    var agree = Golden.tsv("diff", "agree.tsv");
    eq(30, agree.size());
    try (var sb = new Sandbox(false)) {
      for (var row : agree) {
        String name = row.get("name");
        Cli.Result r = runPair(sb, name);
        eq(Integer.parseInt(row.get("exit")), r.code(), name);
        eq(Golden.read("diff", name + ".diff"), r.out(), name);
        eq(0, r.err().length, name);
      }
    }
  }

  static void s11_2_tiePairsSameSizeDifferentChoice() throws Exception {
    var tie = Golden.tsv("diff", "tie.tsv");
    eq(3, tie.size());
    try (var sb = new Sandbox(false)) {
      for (var row : tie) {
        String name = row.get("name");
        byte[] out = runPair(sb, name).out();
        String text = new String(out, ISO_8859_1);
        var body = Arrays.stream(text.split("\n"))
            .filter(l -> !l.startsWith("---") && !l.startsWith("+++"))
            .toList();
        eq(row.get("minus"), String.valueOf(body.stream()
            .filter(l -> l.startsWith("-")).count()), name);
        eq(row.get("plus"), String.valueOf(body.stream()
            .filter(l -> l.startsWith("+")).count()), name);
        ok(!Arrays.equals(out, Golden.read("diff", name + ".diff")),
            name + " — 분류가 틀렸다");
      }
    }
  }

  static List<String> lines(String s) {
    return Diff.splitLines(s.getBytes(ISO_8859_1));
  }

  static void s11_1_linesKeepTheirNewline() {
    eq(List.of("a\n", "b\n", "c"), lines("a\nb\nc"));
    eq(List.of(), lines(""));
    eq(List.of("\n"), lines("\n"));
  }

  static void s11_2_minimalEditCount() {
    var ab = Diff.myers(lines("a\nb\nc\na\nb\nb\na\n"),
        lines("c\nb\na\nb\na\nc\n"));
    // Myers 논문 그림 1 의 예 — 가장 짧은 편집 스크립트는 5
    int n = 0;
    for (boolean[] r : ab) {
      for (boolean x : r) n += x ? 1 : 0;
    }
    eq(5, n);
  }

  static void s11_3_hunkHeaderCounts() {
    String text = Diff.unifiedDiff(lines("x\n"), List.of());
    ok(text.startsWith("@@ -1 +0,0 @@\n"), text);
    text = Diff.unifiedDiff(List.of(), lines("x\ny\n"));
    ok(text.startsWith("@@ -0,0 +1,2 @@\n"), text);
  }

  static void s11_3_identicalInputsHaveNoHunks() {
    eq("", Diff.unifiedDiff(lines("same\n"), lines("same\n")));
  }
}
