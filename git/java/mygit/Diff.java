package mygit;

import static java.nio.charset.StandardCharsets.ISO_8859_1;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

// diff (SPEC.md §11) — 두 줄 목록 사이의 가장 짧은 편집 스크립트.
//
// 세 단계다. (1) 앞뒤의 같은 줄을 떼어 둔다. (2) 남은 가운데서 Myers 의
// 탐욕 탐색으로 가장 짧은 스크립트를 찾는다. (3) 바뀐 줄 묶음을 git
// 처럼 위아래로 밀어 자리를 정한다 — 같은 줄이 되풀이되는 곳에서는
// 어디를 바뀐 줄로 칠지가 여럿이라, 이 단계가 없으면 git 과 덩어리
// 자리가 달라진다. 다섯 언어가 같은 세 단계를 밟는다.
//
// 줄은 바이트 문자열(latin1)이고 줄바꿈까지 품는다 — 끝 줄바꿈이 없는
// 줄은 있는 줄과 다른 줄이다. equals 가 곧 바이트 비교다. rchg 는
// 줄마다 "바뀌었나" 의 boolean 배열이다. 출력도 바이트 문자열이다.
public final class Diff {
  private static final int CONTEXT = 3;
  private static final int BINARY_PROBE = 8000;

  private Diff() {}

  // 파일 하나의 한쪽 — 모드, blob 이름, 바이트
  public record Side(int mode, String oid, byte[] data) {}

  // 바뀐 곳 — a 자리, b 자리, a 줄 수, b 줄 수
  public record Change(int i1, int i2, int n1, int n2) {}

  // 바이트 → 줄 목록. 줄마다 '\n' 을 품고, 마지막 줄만 없을 수 있다.
  public static List<String> splitLines(byte[] data) {
    List<String> out = new ArrayList<>();
    String s = new String(data, ISO_8859_1);
    for (int i = 0; i < s.length();) {
      int nl = s.indexOf('\n', i);
      int end = nl < 0 ? s.length() : nl + 1;
      out.add(s.substring(i, end));
      i = end;
    }
    return out;
  }

  // ── 2 단계: Myers 앞방향 탐욕 탐색 (SPEC.md §11.2) ────────────────

  // 가운데 a·b 의 {ra, rb}. 대각선 k 마다 가장 멀리 간 x 를 V[k] 에.
  //
  // k 는 −d‥d 라 배열 첨자로 쓰려고 off 만큼 민다. d 마다 V 의 사본을
  // 남겨 두었다가 (N, M) 에서 거꾸로 같은 판정을 되밟아 편집을
  // 표시한다. O((N+M)·D) 시간, O((N+M)·D) 공간.
  private static boolean[][] forward(List<String> a, List<String> b) {
    int n = a.size();
    int m = b.size();
    int off = n + m + 1;
    int[] v = new int[2 * off + 1];
    List<int[]> trace = new ArrayList<>();
    for (int d = 0; d <= n + m; d++) {
      trace.add(v.clone());
      for (int k = -d; k <= d; k += 2) {
        int x = k == -d || (k != d && v[off + k - 1] < v[off + k + 1])
            ? v[off + k + 1]                 // 아래로: b 의 줄을 끼움
            : v[off + k - 1] + 1;            // 오른쪽: a 의 줄을 지움
        int y = x - k;
        while (x < n && y < m && a.get(x).equals(b.get(y))) {
          x++;
          y++;
        }
        v[off + k] = x;
        if (x >= n && y >= m) return backtrack(trace, n, m, d, off);
      }
    }
    throw new IllegalStateException("Myers 탐색이 끝나지 않았다");
  }

  private static boolean[][] backtrack(List<int[]> trace, int n, int m,
      int dfin, int off) {
    boolean[] ra = new boolean[n];
    boolean[] rb = new boolean[m];
    int x = n;
    int y = m;
    for (int d = dfin; d > 0; d--) {
      int[] v = trace.get(d);
      int k = x - y;
      boolean down = k == -d
          || (k != d && v[off + k - 1] < v[off + k + 1]);
      int pk = down ? k + 1 : k - 1;
      int px = v[off + pk];
      int py = px - pk;
      if (down) rb[py] = true;
      else ra[px] = true;
      x = px;
      y = py;
    }
    return new boolean[][] {ra, rb};
  }

  // 1·2 단계 — 앞뒤를 깎고 가운데를 앞방향 Myers 로. {ra, rb}.
  public static boolean[][] myers(List<String> a, List<String> b) {
    int n = a.size();
    int m = b.size();
    int s = 0;
    while (s < n && s < m && a.get(s).equals(b.get(s))) s++;
    int e = 0;
    while (e < n - s && e < m - s
        && a.get(n - 1 - e).equals(b.get(m - 1 - e))) {
      e++;
    }
    boolean[][] mid = forward(a.subList(s, n - e), b.subList(s, m - e));
    boolean[] ra = new boolean[n];
    boolean[] rb = new boolean[m];
    System.arraycopy(mid[0], 0, ra, s, mid[0].length);
    System.arraycopy(mid[1], 0, rb, s, mid[1].length);
    return new boolean[][] {ra, rb};
  }

  // ── 3 단계: 밀어 붙이기 (git 의 xdl_change_compact, 휴리스틱 없이) ─

  // 바뀐 줄 묶음 [start, end). 빈 묶음(start == end)도 자리다. chg
  // 끝에는 바뀌지 않은 가짜 줄이 하나 붙어 있다.
  private static final class Group {
    int start;
    int end;
    private final boolean[] chg;
    private final int n;

    Group(boolean[] chg) {
      this.chg = chg;
      n = chg.length - 1;
      while (end < n && chg[end]) end++;
    }

    boolean next() {
      if (end == n) return false;
      start = end = end + 1;
      while (end < n && chg[end]) end++;
      return true;
    }

    boolean previous() {
      if (start == 0) return false;
      end = start = start - 1;
      while (start > 0 && chg[start - 1]) start--;
      return true;
    }

    boolean slideDown(List<String> recs) {
      if (end >= n || !recs.get(start).equals(recs.get(end))) {
        return false;
      }
      chg[start++] = false;
      chg[end++] = true;
      while (end < n && chg[end]) end++;
      return true;
    }

    boolean slideUp(List<String> recs) {
      if (start == 0
          || !recs.get(start - 1).equals(recs.get(end - 1))) {
        return false;
      }
      chg[--start] = true;
      chg[--end] = false;
      while (start > 0 && chg[start - 1]) start--;
      return true;
    }
  }

  // 한 쪽 파일의 바뀐 줄 묶음을 밀어 자리를 정한다(SPEC.md §11.2).
  //
  // 묶음마다 위로 끝까지, 다시 아래로 끝까지 민다(밀다가 이웃 묶음과
  // 붙으면 처음부터). 상대 파일의 바뀐 묶음과 끝이 맞는 자리가
  // 있었으면 그리로 되올리고, 없으면 맨 아래에 둔다. 상대 쪽 묶음 표지
  // go 는 묶음과 발을 맞춰 움직인다 — 그래서 상대 쪽은 줄 내용이
  // 아니라 바뀜 표시(ochg)만 있으면 된다. O(줄 수 × 미는 거리).
  static boolean[] compact(List<String> recs, boolean[] rchg,
      boolean[] ochg) {
    boolean[] chg = Arrays.copyOf(rchg, rchg.length + 1);
    Group g = new Group(chg);
    Group go = new Group(Arrays.copyOf(ochg, ochg.length + 1));
    for (;;) {
      if (g.end != g.start) slide(recs, g, go);
      if (!g.next()) break;
      go.next();
    }
    return Arrays.copyOf(chg, rchg.length);
  }

  // 묶음 g 하나의 자리를 정한다 — compact 의 한 걸음.
  private static void slide(List<String> recs, Group g, Group go) {
    int earliest;
    int matchEnd;
    int size;
    do {
      size = g.end - g.start;
      matchEnd = -1;
      while (g.slideUp(recs)) go.previous();
      earliest = g.end;
      if (go.end > go.start) matchEnd = g.end;
      while (g.slideDown(recs)) {
        go.next();
        if (go.end > go.start) matchEnd = g.end;
      }
    } while (size != g.end - g.start);
    if (g.end != earliest && matchEnd != -1) {
      while (go.end == go.start) {
        g.slideUp(recs);
        go.previous();
      }
    }
  }

  // 세 단계를 다 거친 {ra, rb} — 계약의 전부(SPEC.md §11.2).
  public static boolean[][] editFlags(List<String> a, List<String> b) {
    boolean[][] r = myers(a, b);
    r[0] = compact(a, r[0], r[1]);
    r[1] = compact(b, r[1], r[0]);
    return r;
  }

  // 바뀐 곳들, 앞에서부터.
  //
  // 끝에서 앞으로 훑으며 같은 자리에서 만나는 지운 묶음과 끼운 묶음을
  // 한 바뀐 곳으로 묶는다(git 의 xdl_build_script).
  public static List<Change> buildChanges(boolean[] ra, boolean[] rb) {
    List<Change> out = new ArrayList<>();
    int i1 = ra.length;
    int i2 = rb.length;
    while (i1 > 0 || i2 > 0) {
      if ((i1 > 0 && ra[i1 - 1]) || (i2 > 0 && rb[i2 - 1])) {
        int l1 = i1;
        int l2 = i2;
        while (i1 > 0 && ra[i1 - 1]) i1--;
        while (i2 > 0 && rb[i2 - 1]) i2--;
        out.add(0, new Change(i1, i2, l1 - i1, l2 - i2));
      } else {
        i1--;
        i2--;
      }
    }
    return out;
  }

  // git 기본 드라이버의 함수 줄 — 첫 바이트가 영문자·'_'·'$'.
  private static boolean isFunc(String line) {
    return line.matches("(?s)[A-Za-z_$].*");
  }

  // ASCII 공백만 뗀다(Python 의 bytes.rstrip). stripTrailing 은 쓰지
  // 않는다 — 0x1c‥0x1f 도 떼는데 git 은 그러지 않는다.
  private static String rstrip(String s) {
    return s.replaceAll("[ \\t\\n\\x0b\\f\\r]+$", "");
  }

  private static String span(int start, int count) {
    int first = count > 0 ? start + 1 : start;
    return count == 1 ? "" + first : first + "," + count;
  }

  // 덩어리들(SPEC.md §11.3). 같으면 "".
  public static String unifiedDiff(List<String> a, List<String> b) {
    boolean[][] r = editFlags(a, b);
    List<Change> ch = buildChanges(r[0], r[1]);
    List<String> out = new ArrayList<>();
    for (int i = 0; i < ch.size();) {
      int j = i;
      while (j + 1 < ch.size() && ch.get(j + 1).i1()
          - (ch.get(j).i1() + ch.get(j).n1()) <= 2 * CONTEXT) {
        j++;
      }
      Change first = ch.get(i);
      Change last = ch.get(j);
      int s1 = Math.max(first.i1() - CONTEXT, 0);
      int s2 = Math.max(first.i2() - CONTEXT, 0);
      int e1 = Math.min(last.i1() + last.n1() + CONTEXT, a.size());
      int e2 = Math.min(last.i2() + last.n2() + CONTEXT, b.size());
      String func = "";
      for (int q = s1 - 1; q >= 0; q--) {
        if (isFunc(a.get(q))) {
          String t = rstrip(a.get(q));
          func = " " + rstrip(t.substring(0, Math.min(80, t.length())));
          break;
        }
      }
      out.add("@@ -" + span(s1, e1 - s1) + " +" + span(s2, e2 - s2)
          + " @@" + func + "\n");
      int p1 = s1;
      for (Change c : ch.subList(i, j + 1)) {
        a.subList(p1, c.i1()).forEach(l -> out.add(" " + l));
        a.subList(c.i1(), c.i1() + c.n1())
            .forEach(l -> out.add("-" + l));
        b.subList(c.i2(), c.i2() + c.n2())
            .forEach(l -> out.add("+" + l));
        p1 = c.i1() + c.n1();
      }
      a.subList(p1, e1).forEach(l -> out.add(" " + l));
      i = j + 1;
    }
    StringBuilder sb = new StringBuilder();
    for (String line : out) {
      sb.append(line);
      if (!line.endsWith("\n")) {
        sb.append("\n\\ No newline at end of file\n");
      }
    }
    return sb.toString();
  }

  private static String octal(int mode) {
    return String.format("%06o", mode);
  }

  private static String q(String prefix, String path) {
    return Worktree.quotePath(prefix + path);
  }

  private static boolean binary(byte[] d) {
    for (int i = 0; i < Math.min(d.length, BINARY_PROBE); i++) {
      if (d[i] == 0) return true;
    }
    return false;
  }

  // 파일 하나의 diff 전체(SPEC.md §11.4). old·nu 는 Side 또는
  // null(새로 생김·지워짐). 경로는 바이트 문자열. 같으면 "".
  public static String fileDiff(String pathA, String pathB, Side old,
      Side nu) {
    if (old != null && nu != null && old.mode() == nu.mode()
        && old.oid().equals(nu.oid())) {
      return "";
    }
    List<String> rows = new ArrayList<>(List.of("diff --git "
        + q("a/", pathA) + " " + q("b/", pathB)));
    String z = "0000000";
    if (old == null) {
      rows.add("new file mode " + octal(nu.mode()));
      rows.add("index " + z + ".." + nu.oid().substring(0, 7));
    } else if (nu == null) {
      rows.add("deleted file mode " + octal(old.mode()));
      rows.add("index " + old.oid().substring(0, 7) + ".." + z);
    } else {
      if (old.mode() != nu.mode()) {
        rows.add("old mode " + octal(old.mode()));
        rows.add("new mode " + octal(nu.mode()));
      }
      if (old.oid().equals(nu.oid())) {             // 모드만 바뀜
        return String.join("\n", rows) + "\n";
      }
      rows.add("index " + old.oid().substring(0, 7) + ".."
          + nu.oid().substring(0, 7)
          + (old.mode() == nu.mode() ? " " + octal(old.mode()) : ""));
    }
    byte[] da = old == null ? new byte[0] : old.data();
    byte[] db = nu == null ? new byte[0] : nu.data();
    String nameA = old == null ? "/dev/null" : q("a/", pathA);
    String nameB = nu == null ? "/dev/null" : q("b/", pathB);
    if (binary(da) || binary(db)) {
      rows.add("Binary files " + nameA + " and " + nameB + " differ");
      return String.join("\n", rows) + "\n";
    }
    rows.add("--- " + nameA);
    rows.add("+++ " + nameB);
    return String.join("\n", rows) + "\n"
        + unifiedDiff(splitLines(da), splitLines(db));
  }

  // 저장소의 blob 에서 한쪽을.
  public static Side blobSide(String gitdir, int mode, String oid) {
    return new Side(mode, oid, Objects.readObject(gitdir, oid).body());
  }
}
