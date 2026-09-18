package mygit.tests;

import static java.nio.charset.StandardCharsets.ISO_8859_1;
import static mygit.tests.Check.eq;

import mygit.Merge;

// 3-way 파일 합치기의 시험 — SPEC.md §12.3, 10단계.
//
// 큰 오라클은 golden/scen/merge-*.scn 14장면(진짜 git merge 의 작업
// 트리 파일·인덱스·MERGE_MSG·머지 커밋 이름)이다. 여기서는 merge3
// 하나를 따로 부른다 — 장면의 세 판을 그대로 넣고, 장면에서 git 이
// 남긴 파일 내용과 같은지 본다. 규칙마다 한 장면이 증거다.
final class MergeTest {
  private MergeTest() {}

  // 재료 셋 → "합친 글자|충돌 수"
  static String merge(String base, String ours, String theirs)
      throws Exception {
    Merge.Merged m = Merge.merge3(Golden.make(base), Golden.make(ours),
        Golden.make(theirs), "t");
    return new String(m.text(), ISO_8859_1) + "|" + m.conflicts();
  }

  static void s12_3_adjacentLinesConflict() throws Exception {
    // merge-adjacent.scn — 둘째 줄과 셋째 줄을 따로 고쳐도 충돌
    eq("a\n<<<<<<< HEAD\nB\nc\n=======\nb\nC\n>>>>>>> t\nd\n|1",
        merge("text:a\\nb\\nc\\nd\\n", "text:a\\nB\\nc\\nd\\n",
            "text:a\\nb\\nC\\nd\\n"));
  }

  static void s12_3_oneLineApartIsClean() throws Exception {
    eq("a\nB\nc\nD\ne\n|0", merge("text:a\\nb\\nc\\nd\\ne\\n",
        "text:a\\nB\\nc\\nd\\ne\\n", "text:a\\nb\\nc\\nD\\ne\\n"));
  }

  static void s12_3_refineKeepsCommonLinesOutside() throws Exception {
    eq("a\nq\n<<<<<<< HEAD\nw\n=======\nr\n>>>>>>> t\ne\nz\n|1",
        merge("text:a\\nb\\nz\\n", "text:a\\nq\\nw\\ne\\nz\\n",
            "text:a\\nq\\nr\\ne\\nz\\n"));
  }

  static void s12_3_threeLinesApartJoinFourSplit() throws Exception {
    eq(true, merge("text:a\\nb\\nm1\\nm2\\nm3\\nd\\ne\\n",
        "text:a\\n1\\nm1\\nm2\\nm3\\n2\\ne\\n",
        "text:a\\n3\\nm1\\nm2\\nm3\\n4\\ne\\n").endsWith("|1"));
    eq(true, merge("text:a\\nb\\nm1\\nm2\\nm3\\nm4\\nd\\ne\\n",
        "text:a\\n1\\nm1\\nm2\\nm3\\nm4\\n2\\ne\\n",
        "text:a\\n3\\nm1\\nm2\\nm3\\nm4\\n4\\ne\\n").endsWith("|2"));
  }

  static void s12_1_unbornHeadIsRefused() throws Exception {
    // 첫 커밋 전 — git 은 <b> 를 그대로 가져오지만 mygit 은 줄인다
    try (var sb = new Sandbox(false)) {
      sb.mygit("init");
      String tree = sb.out("write-tree").strip();
      String other = sb.out("commit-tree", tree, "-m", "x").strip();
      eq("128 fatal: mygit: nothing to merge into yet",
          Sandbox.firstLine(sb.mygit("merge", other)));
    }
  }

  static void s12_3_identicalChangeTakenOnce() throws Exception {
    eq("1\nX\n3\n4\nY\n|0", merge("seq:1:5",
        "text:1\\nX\\n3\\n4\\n5\\n", "text:1\\nX\\n3\\n4\\nY\\n"));
  }
}
