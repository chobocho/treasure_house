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

  // 가장 좋은 공통 조상들(SPEC.md §10.2), 커미터 날짜 내림차순.
  //
  // 공통 조상 가운데 다른 공통 조상의 조상이 아닌 것만 남긴다. 작은
  // 저장소를 위한 곧은 방법이다 — git 은 날짜로 칠하며 내려가는 더
  // 빠른 길(paint_down_to_common)을 쓴다. O(커밋 수²) 최악.
  public static List<String> mergeBases(String gitdir, String a,
      String b) {
    Set<String> common = ancestors(gitdir, a);
    common.retainAll(ancestors(gitdir, b));
    Set<String> below = new HashSet<>();
    for (String c : common) {
      for (String p : node(gitdir, c).parents()) {
        below.addAll(ancestors(gitdir, p));
      }
    }
    return common.stream().filter(c -> !below.contains(c))
        .sorted(Comparator.comparingLong(c -> -node(gitdir, c).date()))
        .toList();
  }
}
