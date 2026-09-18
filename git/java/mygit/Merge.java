package mygit;

import static java.nio.charset.StandardCharsets.ISO_8859_1;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;
import java.util.TreeSet;
import mygit.Diff.Change;
import mygit.Worktree.Stat;

// merge (SPEC.md §12) — 공통 조상 B 에서 갈라진 O(우리)와 T(그들).
//
// 파일 하나의 합치기는 git 의 xdl_merge(ZEALOUS 수준)를 따른다:
//   1. B→O, B→T 의 바뀐 곳을 B 좌표로 짝지어 훑는다. 엄격히 앞선 쪽은
//      그대로 받고, 겹치거나 **맞닿으면** 충돌 후보다(같은 수정이면
//      한 번만).
//   2. 충돌마다 O 쪽과 T 쪽을 다시 diff 해 같은 줄을 표지 밖으로 뺀다.
//   3. 사이가 바뀌지 않은 줄 3개 이하인 이웃 충돌은 하나로 붙인다.
// 진짜 git merge 로 경계를 확인한 규칙들이다(golden/scen/merge-*.scn).
// 줄은 diff 와 같은 바이트 문자열이다.
public final class Merge {
  private static final int JOIN = 3;   // 이만큼 가까운 충돌은 붙인다

  private Merge() {}

  public record Merged(byte[] text, int conflicts) {}

  // 조각 — 's' 바뀌지 않은 줄, 'c' 한쪽 변경을 받은 줄(o 에), 'x'
  // 충돌(O 줄들 o, T 줄들 t)
  private record Piece(char kind, List<String> o, List<String> t) {}

  // 짝 맞추기의 한 칸 — 'o'(O 쪽 변경 받기)·'t'·'c'(충돌 후보), B 의
  // [start, end), 그리고 받을 줄들
  private record Pair(char kind, int start, int end, List<String> o,
      List<String> t) {}

  private static List<Change> changes(List<String> a, List<String> b) {
    boolean[][] r = Diff.editFlags(a, b);
    return Diff.buildChanges(r[0], r[1]);
  }

  // B 의 [start, end) 에 맞는 한쪽 파일의 범위 {시작, 끝}.
  //
  // start 앞에서 시작한 바뀐 곳들의 길이 차를 더하면 시작 자리가,
  // end 이하에서 시작한 것까지 더하면 끝 자리가 나온다 — 이 범위에
  // 걸친 바뀐 곳은 짝 맞추기가 전부 이 범위에 넣어 두었다.
  private static int[] sideRange(List<Change> cs, int start, int end) {
    int s = start;
    int e = end;
    for (Change c : cs) {
      if (c.i1() < start) s += c.n2() - c.n1();
      if (c.i1() <= end) e += c.n2() - c.n1();
    }
    return new int[] {s, e};
  }

  private static List<String> lines(List<String> side, Change c) {
    return side.subList(c.i2(), c.i2() + c.n2());
  }

  // 1 단계 — 짝 맞추기. 바뀌지 않은 곳은 빠진다.
  private static List<Pair> pair(List<String> base, List<String> ours,
      List<String> theirs) {
    List<Change> c1 = changes(base, ours);
    List<Change> c2 = changes(base, theirs);
    List<Pair> out = new ArrayList<>();
    int i = 0;
    int j = 0;
    while (i < c1.size() || j < c2.size()) {
      Change x = i < c1.size() ? c1.get(i) : null;
      Change y = j < c2.size() ? c2.get(j) : null;
      if (y == null || (x != null && x.i1() + x.n1() < y.i1())) {
        out.add(new Pair('o', x.i1(), x.i1() + x.n1(), lines(ours, x),
            null));
        i++;
      } else if (x == null || y.i1() + y.n1() < x.i1()) {
        out.add(new Pair('t', y.i1(), y.i1() + y.n1(), null,
            lines(theirs, y)));
        j++;
      } else if (x.i1() == y.i1() && x.n1() == y.n1()
          && lines(ours, x).equals(lines(theirs, y))) {
        out.add(new Pair('o', x.i1(), x.i1() + x.n1(), lines(ours, x),
            null));                      // 양쪽이 같은 수정 — 한 번만
        i++;
        j++;
      } else {
        int start = Math.min(x.i1(), y.i1());
        int end = Math.max(x.i1() + x.n1(), y.i1() + y.n1());
        i++;
        j++;
        for (;;) {                        // 맞닿는 것까지 넓힌다
          if (i < c1.size() && c1.get(i).i1() <= end) {
            end = Math.max(end, c1.get(i).i1() + c1.get(i).n1());
            i++;
          } else if (j < c2.size() && c2.get(j).i1() <= end) {
            end = Math.max(end, c2.get(j).i1() + c2.get(j).n1());
            j++;
          } else {
            break;
          }
        }
        int[] os = sideRange(c1, start, end);
        int[] ts = sideRange(c2, start, end);
        out.add(new Pair('c', start, end, ours.subList(os[0], os[1]),
            theirs.subList(ts[0], ts[1])));
      }
    }
    return out;
  }

  // 2 단계 — 충돌 하나를 O·T 의 diff 로 쪼갠다. 같은 줄은 표지
  // 밖으로 나온다. O == T 면 충돌이 아니다.
  private static List<Piece> refine(List<String> o, List<String> t) {
    List<Piece> out = new ArrayList<>();
    if (o.equals(t)) {
      out.add(new Piece('s', o, null));
      return out;
    }
    int p1 = 0;
    for (Change c : changes(o, t)) {
      if (c.i1() > p1) {
        out.add(new Piece('s', o.subList(p1, c.i1()), null));
      }
      out.add(new Piece('x', o.subList(c.i1(), c.i1() + c.n1()),
          lines(t, c)));
      p1 = c.i1() + c.n1();
    }
    if (p1 < o.size()) out.add(new Piece('s', o.subList(p1, o.size()),
        null));
    return out;
  }

  private static List<String> cat(List<String> a, List<String> b) {
    List<String> out = new ArrayList<>(a);
    out.addAll(b);
    return out;
  }

  // 세 판의 바이트 → (합친 바이트, 충돌 수). SPEC.md §12.3.
  //
  // O(줄 수 × 편집 거리) — diff 두 번과 충돌마다 diff 한 번.
  public static Merged merge3(byte[] base, byte[] ours, byte[] theirs,
      String label) {
    if (Arrays.equals(ours, theirs) || Arrays.equals(base, theirs)) {
      return new Merged(ours, 0);
    }
    if (Arrays.equals(base, ours)) return new Merged(theirs, 0);
    List<String> b = Diff.splitLines(base);
    List<Piece> pieces = new ArrayList<>();
    int pos = 0;
    for (Pair p : pair(b, Diff.splitLines(ours),
        Diff.splitLines(theirs))) {
      if (p.start() > pos) {
        pieces.add(new Piece('s', b.subList(pos, p.start()), null));
      }
      switch (p.kind()) {
        case 'o' -> pieces.add(new Piece('c', p.o(), null));
        case 't' -> pieces.add(new Piece('c', p.t(), null));
        default -> pieces.addAll(refine(p.o(), p.t()));
      }
      pos = p.end();
    }
    if (pos < b.size()) {
      pieces.add(new Piece('s', b.subList(pos, b.size()), null));
    }
    // 3 단계 — 바뀌지 않은 줄 JOIN 개 이하로 떨어진 충돌을 붙인다
    List<Piece> joined = new ArrayList<>();
    for (Piece p : pieces) {
      int n = joined.size();
      boolean near = n >= 2 && joined.get(n - 1).kind() == 's'
          && joined.get(n - 2).kind() == 'x'
          && joined.get(n - 1).o().size() <= JOIN;
      if (p.kind() == 'x' && near) {
        List<String> mid = joined.remove(n - 1).o();
        Piece prev = joined.remove(n - 2);
        p = new Piece('x', cat(cat(prev.o(), mid), p.o()),
            cat(cat(prev.t(), mid), p.t()));
      } else if (p.kind() == 's' && n > 0
          && joined.get(n - 1).kind() == 's') {
        p = new Piece('s', cat(joined.remove(n - 1).o(), p.o()), null);
      }
      joined.add(p);
    }
    StringBuilder out = new StringBuilder();
    int conflicts = 0;
    for (Piece p : joined) {
      if (p.kind() == 'x') {
        conflicts++;
        out.append("<<<<<<< HEAD\n");
        p.o().forEach(out::append);
        out.append("=======\n");
        p.t().forEach(out::append);
        out.append(">>>>>>> ").append(label).append('\n');
      } else {
        p.o().forEach(out::append);
      }
    }
    return new Merged(out.toString().getBytes(ISO_8859_1), conflicts);
  }

  // 트리 단위 합치기의 결과 한 칸. stat 이 null 이면 지움, stages 가
  // 있으면 충돌 — 그때 text 는 표지가 든 내용, stat 의 모드는 작업
  // 트리에 쓸 모드(이름은 없다).
  public record Outcome(Stat stat, byte[] text,
      Map<Integer, Stat> stages) {}

  // 합치기 전체 — 경로마다의 결과, 안내 줄들, 충돌 경로들
  public record TreeMerge(Map<String, Outcome> result,
      List<String> notes, List<String> conflicts) {}

  // 세 줄 규칙이 못 고름. 없음(null)도 값이라 따로 표지가 있어야
  // 한다 — 한쪽만 지웠으면 지움이 이긴다.
  private static final Object UNDECIDED = new Object();

  private static Object pick(Object bv, Object ov, Object tv) {
    if (java.util.Objects.equals(ov, tv)
        || java.util.Objects.equals(bv, tv)) {
      return ov;
    }
    return java.util.Objects.equals(bv, ov) ? tv : UNDECIDED;
  }

  private static GitError unsupported(String what, String path) {
    return new GitError("fatal: mygit: unsupported merge case (" + what
        + ") in " + path);
  }

  // 트리 단위 합치기(SPEC.md §12.2). base·ours·theirs 는 {경로: (모드,
  // 이름)}. 모드는 내용과 따로 같은 세 줄 규칙.
  public static TreeMerge mergeTrees(String gitdir,
      Map<String, Stat> base, Map<String, Stat> ours,
      Map<String, Stat> theirs, String label) {
    Map<String, Outcome> result = new TreeMap<>();
    List<String> notes = new ArrayList<>();
    List<String> conflicts = new ArrayList<>();
    TreeSet<String> paths = new TreeSet<>(base.keySet());
    paths.addAll(ours.keySet());
    paths.addAll(theirs.keySet());
    for (String p : paths) {
      Stat bv = base.get(p);
      Stat ov = ours.get(p);
      Stat tv = theirs.get(p);
      Object whole = pick(bv, ov, tv);
      if (whole != UNDECIDED) {
        result.put(p, new Outcome((Stat) whole, null, null));
        continue;
      }
      if (ov == null || tv == null) {
        throw unsupported("modify/delete", p);
      }
      Object mode = pick(bv == null ? null : bv.mode(), ov.mode(),
          tv.mode());
      if (mode == UNDECIDED) throw unsupported("mode", p);
      notes.add("Auto-merging " + p);
      byte[][] data = new byte[3][];
      Stat[] sides = {bv, ov, tv};
      for (int k = 0; k < 3; k++) {
        data[k] = sides[k] == null ? new byte[0]
            : Objects.readObject(gitdir, sides[k].oid()).body();
      }
      Merged m = merge3(data[0], data[1], data[2], label);
      if (m.conflicts() == 0) {
        String oid = Objects.writeObject(gitdir, "blob", m.text());
        result.put(p, new Outcome(new Stat((Integer) mode, oid), null,
            null));
        continue;
      }
      notes.add("CONFLICT (" + (bv == null ? "add/add" : "content")
          + "): Merge conflict in " + p);
      Map<Integer, Stat> stages = new TreeMap<>();
      for (int k = 0; k < 3; k++) {
        if (sides[k] != null) stages.put(k + 1, sides[k]);
      }
      result.put(p, new Outcome(new Stat((Integer) mode, null),
          m.text(), stages));
      conflicts.add(p);
    }
    return new TreeMerge(result, notes, conflicts);
  }
}
