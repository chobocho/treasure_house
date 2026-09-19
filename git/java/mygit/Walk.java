package mygit;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.PriorityQueue;
import java.util.Set;

// 역사 걷기와 merge-base (SPEC.md §10).
//
// git 의 기본 log 차례는 "커미터 날짜가 늦은 것부터" 인데, 날짜가 같을
// 때의 규칙까지 정해져 있다 — 날짜 차례로 정렬된 목록에 새 커밋을 끼울
// 때 **같은 날짜들 가운데 맨 뒤에** 끼운다(git 의 commit_list_insert_
// by_date). 이 덱의 저장소는 모든 커밋의 날짜가 같게 만들어지므로, 이
// 한 줄이 차례의 전부를 정한다(golden/dag/equal 이 그것을 확인한다).
public final class Walk {
  private Walk() {}

  // 커밋 하나에서 걷기에 필요한 것 — 부모 목록과 커미터 날짜(초)
  private record Node(List<String> parents, long date) {}

  private static final Map<String, Node> CACHE = new HashMap<>();

  // 한 번 읽은 커밋은 기억한다. 열쇠가 이름뿐이어도 되는 까닭: 이름이
  // 같으면 내용도 같다 — 어느 저장소에서 읽었든.
  private static Node node(String gitdir, String oid) {
    return CACHE.computeIfAbsent(oid, k -> {
      Commit.CommitObj c = Commit.parseCommit(
          Objects.readObject(gitdir, oid).body());
      return new Node(c.parents(),
          Commit.parseIdent(c.committer()).secs());
    });
  }

  // 큐에 들어간 커밋 — 날짜와 들어온 차례
  private record Queued(String oid, long date, long seq) {}

  // 시작 커밋들에서 닿는 커밋 전부, git log 의 기본 차례로.
  //
  // "날짜 내림차순 목록의 같은 날짜 맨 뒤에 끼우기" 는 곧 (날짜
  // 내림차순, 들어온 차례 오름차순) 우선순위 큐다 — 목록 끼우기의
  // O(큐 길이) 대신 O(log 큐 길이). 전체 O(커밋 수 × log).
  public static List<String> walkLog(String gitdir,
      List<String> starts) {
    PriorityQueue<Queued> queue = new PriorityQueue<>(Comparator
        .comparingLong((Queued q) -> -q.date())
        .thenComparingLong(Queued::seq));
    Set<String> seen = new HashSet<>();
    List<String> out = new ArrayList<>();
    for (String s : starts) push(gitdir, queue, seen, s);
    while (!queue.isEmpty()) {
      String oid = queue.poll().oid();
      out.add(oid);
      for (String p : node(gitdir, oid).parents()) {
        push(gitdir, queue, seen, p);
      }
    }
    return out;
  }

  private static void push(String gitdir, PriorityQueue<Queued> queue,
      Set<String> seen, String oid) {
    if (seen.add(oid)) {
      queue.add(new Queued(oid, node(gitdir, oid).date(), seen.size()));
    }
  }

  // oid 와 그 조상 전부의 집합. O(커밋 수).
  static Set<String> ancestors(String gitdir, String oid) {
    Set<String> seen = new HashSet<>();
    ArrayDeque<String> stack = new ArrayDeque<>(List.of(oid));
    while (!stack.isEmpty()) {
      String c = stack.pop();
      if (seen.add(c)) stack.addAll(node(gitdir, c).parents());
    }
    return seen;
  }

  // a 가 b 이거나 b 의 조상인가.
  public static boolean isAncestor(String gitdir, String a, String b) {
    return ancestors(gitdir, b).contains(a);
  }

  // 큐 한 칸 — 날짜 내림차순, 같으면 넣은 차례(seq)가 빠른 것이 먼저.
  private record Slot(String oid, long date, long seq) {}

  // git 의 paint_down_to_common(commit-reach.c)이 공통 조상 후보를 찾는
  // 차례 — SPEC.md §10.2 의 1~4. 표시는 P1(a 에서 닿음)·P2(b 에서
  // 닿음)·STALE(이미 찾은 후보의 조상). "넣을 때 STALE 이 아니었던"
  // 커밋이 큐에 남아 있는 동안 돈다(git 의 max_nonstale).
  // O(커밋 수 × log 커밋 수) 시간, O(커밋 수) 공간.
  private static List<String> paint(String gitdir, String a, String b) {
    final int p1 = 1, p2 = 2, stale = 4;
    Map<String, Integer> flags = new HashMap<>();
    // 큐에 있는 것 → 넣을 때 STALE 이 아니었나
    Map<String, Boolean> queued = new HashMap<>();
    PriorityQueue<Slot> q = new PriorityQueue<>(
        Comparator.comparingLong((Slot x) -> -x.date())
            .thenComparingLong(Slot::seq));
    long[] seq = {0};
    int[] live = {0};
    java.util.function.Consumer<String> put = c -> {
      if (queued.containsKey(c)) return;           // 자리는 그대로
      boolean fresh = (flags.getOrDefault(c, 0) & stale) == 0;
      queued.put(c, fresh);
      if (fresh) live[0]++;
      q.add(new Slot(c, node(gitdir, c).date(), seq[0]++));
    };
    flags.put(a, p1);
    put.accept(a);
    flags.put(b, flags.getOrDefault(b, 0) | p2);
    put.accept(b);
    List<String> found = new ArrayList<>();
    while (live[0] > 0) {
      String c = q.poll().oid();
      if (queued.remove(c)) live[0]--;
      int f = flags.get(c) & (p1 | p2 | stale);
      if (f == (p1 | p2)) {
        if (!found.contains(c)) found.add(c);
        f |= stale;
      }
      for (String p : node(gitdir, c).parents()) {
        int have = flags.getOrDefault(p, 0);
        if ((have & f) == f) continue;
        flags.put(p, have | f);
        put.accept(p);
      }
    }
    List<String> out = new ArrayList<>();
    for (String c : found) {
      if ((flags.get(c) & stale) == 0) out.add(c);
    }
    return out;
  }

  // 가장 좋은 공통 조상들(SPEC.md §10.2) — git 과 같은 차례로.
  //
  // paint 가 찾은 후보에서 다른 후보의 조상인 것을 차례를 지키며 빼고
  // (git 의 remove_redundant), 커미터 날짜 내림차순으로 안정 정렬한다
  // (List.sort 는 안정). 날짜가 같으면 찾은 차례가 남아 인자 순서에
  // 따라 답의 차례가 바뀐다 — git 도 그렇다. O(커밋 수 × 후보 수).
  public static List<String> mergeBases(String gitdir, String a,
      String b) {
    List<String> cands = paint(gitdir, a, b);
    List<String> best = new ArrayList<>();
    for (String c : cands) {
      boolean redundant = false;
      for (String o : cands) {
        if (!o.equals(c) && isAncestor(gitdir, c, o)) {
          redundant = true;
          break;
        }
      }
      if (!redundant) best.add(c);
    }
    best.sort(Comparator.comparingLong(c -> -node(gitdir, c).date()));
    return best;
  }
}
