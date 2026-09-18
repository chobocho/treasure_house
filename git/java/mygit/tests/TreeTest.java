package mygit.tests;

import static java.nio.charset.StandardCharsets.ISO_8859_1;
import static mygit.tests.Check.eq;
import static mygit.tests.Check.ok;

import java.util.ArrayList;
import java.util.List;
import mygit.Cli;
import mygit.Objects;
import mygit.Tree;
import mygit.Tree.Entry;
import mygit.Tree.PathEntry;
import mygit.Worktree;

// tree 의 시험 — SPEC.md §4.3 · §8.2, 4단계 "정렬 규칙이 전부다".
//
// 오라클은 golden/trees/ — 경우마다 진짜 git 이 인덱스에 올린
// (모드·blob·경로) 목록(<경우>.tsv)과 write-tree 의 이름(trees.tsv),
// 그리고 ls-tree -r -t 의 출력(<경우>.ls)이다.
final class TreeTest {
  private TreeTest() {}

  // <경우>.tsv → (모드, blob 이름, 경로 바이트 문자열)
  static List<PathEntry> entriesOf(String name) throws Exception {
    List<PathEntry> out = new ArrayList<>();
    String text = new String(Golden.read("trees", name + ".tsv"),
        ISO_8859_1);
    for (String line : text.split("\n")) {
      if (line.isEmpty() || line.startsWith("#")) continue;
      String[] c = line.split("\t", 3);
      out.add(new PathEntry(c[0], c[1], c[2]));
    }
    return out;
  }

  // ls-tree 가 따옴표로 감싼 경로를 바이트로 되돌린다(시험 전용).
  // \t \n \" \\ 와 세 자리 8진 \ooo 만 나온다(SPEC.md §8.2).
  static String unquote(String p) {
    if (!p.startsWith("\"")) return p;
    StringBuilder out = new StringBuilder();
    for (int i = 1; i < p.length() - 1; i++) {
      char c = p.charAt(i);
      if (c != '\\') {
        out.append(c);
      } else if (Character.isDigit(p.charAt(i + 1))) {
        out.append((char) Integer.parseInt(p.substring(i + 1, i + 4),
            8));
        i += 3;
      } else {
        char n = p.charAt(++i);
        out.append(n == 't' ? '\t' : n == 'n' ? '\n' : n);
      }
    }
    return out.toString();
  }

  // <경우>.ls 의 줄마다 [머리("모드 형식 이름"), 경로]
  static List<String[]> lsLines(String name) throws Exception {
    List<String[]> out = new ArrayList<>();
    for (String line : new String(Golden.read("trees", name + ".ls"),
        ISO_8859_1).split("\n")) {
      if (!line.isEmpty()) out.add(line.split("\t", 2));
    }
    return out;
  }

  static void s4_3_twelveTreesHaveGitNames() throws Exception {
    var cases = Golden.tsv("trees", "trees.tsv");
    eq(12, cases.size());
    ObjectsTest.withRepo(g -> {
      for (var row : cases) {
        eq(row.get("tree"), Tree.writeTree(g,
            entriesOf(row.get("case"))), row.get("case"));
      }
    });
  }

  static void s4_3_everySubtreeGitListedWasWritten() throws Exception {
    ObjectsTest.withRepo(g -> {
      for (var row : Golden.tsv("trees", "trees.tsv")) {
        Tree.writeTree(g, entriesOf(row.get("case")));
        for (String[] l : lsLines(row.get("case"))) {
          String[] meta = l[0].split(" ");
          if (meta[1].equals("tree")) {
            eq("tree", Objects.readObject(g, meta[2]).type(), l[1]);
          }
        }
      }
    });
  }

  static void s4_3_flattenGivesBackTheInput() throws Exception {
    ObjectsTest.withRepo(g -> {
      for (var row : Golden.tsv("trees", "trees.tsv")) {
        var ents = entriesOf(row.get("case"));
        String oid = Tree.writeTree(g, ents);
        eq(ents, Tree.flattenTree(g, oid), row.get("case"));
      }
    });
  }

  static void s4_3_directorySortsAsIfItEndedInSlash() {
    String z = "0".repeat(40);
    var ents = List.of(new Entry("100644", "ab", z),
        new Entry("40000", "a", z), new Entry("100644", "a=b", z),
        new Entry("100644", "a.b", z), new Entry("100644", "a-b", z));
    var names = Tree.parseTree(Tree.serializeTree(ents)).stream()
        .map(Entry::name).toList();
    eq(List.of("a-b", "a.b", "a", "a=b", "ab"), names);
  }

  static void s4_3_plainNameSortWouldBeWrong() {
    // 이름만으로 정렬하면 a 가 맨 앞 — 규칙이 왜 있는지 보여 준다
    ok(Tree.treeEntryKey("100644", "a-b")
        .compareTo(Tree.treeEntryKey("40000", "a")) < 0, "a-b < a/");
    ok(Tree.treeEntryKey("100644", "a")
        .compareTo(Tree.treeEntryKey("100644", "a-b")) < 0, "a < a-b");
  }

  static void s4_3_modeIsNotZeroPaddedInTheBody() {
    byte[] body = Tree.serializeTree(
        List.of(new Entry("40000", "d", "1".repeat(40))));
    ok(new String(body, ISO_8859_1).startsWith("40000 d\0"), "40000");
  }

  static void s4_3_roundTripOnGitTrees() throws Exception {
    int n = 0;
    for (var row : ObjectsTest.objs()) {
      if (!row.get("type").equals("tree")) continue;
      byte[] body = BlobTest.bodyOf(row.get("id"));
      eq(body, Tree.serializeTree(Tree.parseTree(body)));
      n++;
    }
    ok(n >= 2, n);
  }

  static void s8_2_quoting() {
    eq("plain.txt", Worktree.quotePath("plain.txt"));
    eq("sp ace", Worktree.quotePath("sp ace"));
    eq("\"sp ace\"", Worktree.quotePath("sp ace", true));
    eq("\"tab\\tx\"", Worktree.quotePath("tab\tx"));
    eq("\"q\\\"uote\"", Worktree.quotePath("q\"uote"));
    eq("\"back\\\\slash\"", Worktree.quotePath("back\\slash"));
    eq("\"\\355\\225\\234\\352\\270\\200.txt\"",
        Worktree.quotePath(Golden.b("한글.txt")));
    eq("\"del\\177\"", Worktree.quotePath("del" + (char) 127));
  }

  static void s9_catFilePTreeMatchesLsTreeTopLevel() throws Exception {
    try (var sb = new Sandbox(true)) {
      for (var row : Golden.tsv("trees", "trees.tsv")) {
        Tree.writeTree(sb.gitdir, entriesOf(row.get("case")));
        StringBuilder want = new StringBuilder();
        for (String[] l : lsLines(row.get("case"))) {
          if (!unquote(l[1]).contains("/")) {
            want.append(l[0]).append('\t').append(l[1]).append('\n');
          }
        }
        Cli.Result r = sb.mygit("cat-file", "-p", row.get("tree"));
        eq(0, r.code());
        eq(want.toString(), new String(r.out(), ISO_8859_1),
            row.get("case"));
      }
    }
  }
}
