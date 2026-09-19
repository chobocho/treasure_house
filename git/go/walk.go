package mygit

// 역사 걷기와 merge-base (SPEC.md §10).
//
// git 의 기본 log 차례는 "커미터 날짜가 늦은 것부터" 인데, 날짜가 같을
// 때의 규칙까지 정해져 있다 — 날짜 차례로 정렬된 목록에 새 커밋을
// 끼울 때 같은 날짜들 가운데 맨 뒤에 끼운다(git 의 commit_list_
// insert_by_date). 이 덱의 저장소는 모든 커밋의 날짜가 같게 만들어지
// 므로, 이 한 줄이 차례의 전부를 정한다.

import (
	"container/heap"
	"sort"
)

type commitInfo struct {
	parents []string
	when    int64
}

var walkCache = map[[2]string]commitInfo{}

// parentsAndDate 는 (부모 목록, 커미터 날짜 초). 한 번 읽은 커밋은
// 기억한다 — 커밋은 바뀌지 않으니 지울 일이 없다.
func parentsAndDate(gitdir, oid string) (commitInfo, error) {
	key := [2]string{gitdir, oid}
	if ci, ok := walkCache[key]; ok {
		return ci, nil
	}
	_, body, err := ReadObject(gitdir, oid)
	if err != nil {
		return commitInfo{}, err
	}
	c, err := ParseCommit(body)
	if err != nil {
		return commitInfo{}, err
	}
	_, _, when, _, err := ParseIdent(c.Committer)
	if err != nil {
		return commitInfo{}, err
	}
	walkCache[key] = commitInfo{c.Parents, when}
	return walkCache[key], nil
}

// WalkLog 는 시작 커밋들에서 닿는 커밋 전부, git log 의 기본 차례로.
// 큐는 날짜 내림차순 목록이다. 끼울 자리는 "날짜가 같거나 늦은 것들
// 바로 뒤" — 그래서 같은 날짜라면 먼저 들어온 것이 먼저 나간다.
// O(커밋 수 × log(큐 길이)) 비교, 끼우기는 목록이라 O(큐 길이).
func WalkLog(gitdir string, starts []string) ([]string, error) {
	var queue, out []string
	var when []int64
	seen := map[string]bool{}
	push := func(oid string) error {
		if seen[oid] {
			return nil
		}
		seen[oid] = true
		ci, err := parentsAndDate(gitdir, oid)
		if err != nil {
			return err
		}
		at := sort.Search(len(when), func(i int) bool {
			return when[i] < ci.when
		})
		when = append(when[:at], append([]int64{ci.when},
			when[at:]...)...)
		queue = append(queue[:at], append([]string{oid},
			queue[at:]...)...)
		return nil
	}
	for _, s := range starts {
		if err := push(s); err != nil {
			return nil, err
		}
	}
	for len(queue) > 0 {
		oid := queue[0]
		queue, when = queue[1:], when[1:]
		out = append(out, oid)
		ci, _ := parentsAndDate(gitdir, oid)
		for _, p := range ci.parents {
			if err := push(p); err != nil {
				return nil, err
			}
		}
	}
	return out, nil
}

// ancestors 는 oid 와 그 조상 전부의 집합. O(커밋 수).
func ancestors(gitdir, oid string) (map[string]bool, error) {
	seen := map[string]bool{}
	stack := []string{oid}
	for len(stack) > 0 {
		c := stack[len(stack)-1]
		stack = stack[:len(stack)-1]
		if seen[c] {
			continue
		}
		seen[c] = true
		ci, err := parentsAndDate(gitdir, c)
		if err != nil {
			return nil, err
		}
		stack = append(stack, ci.parents...)
	}
	return seen, nil
}

// IsAncestor 는 a 가 b 이거나 b 의 조상인가.
func IsAncestor(gitdir, a, b string) (bool, error) {
	anc, err := ancestors(gitdir, b)
	return anc[a], err
}

// paintItem 은 paint 의 우선순위 큐 한 칸 — 날짜 내림차순, 같으면
// 넣은 차례(seq)가 빠른 것이 먼저.
type paintItem struct {
	oid  string
	when int64
	seq  int
}

type paintQueue []paintItem

func (q paintQueue) Len() int { return len(q) }
func (q paintQueue) Less(i, j int) bool {
	if q[i].when != q[j].when {
		return q[i].when > q[j].when
	}
	return q[i].seq < q[j].seq
}
func (q paintQueue) Swap(i, j int) { q[i], q[j] = q[j], q[i] }
func (q *paintQueue) Push(x any)   { *q = append(*q, x.(paintItem)) }
func (q *paintQueue) Pop() any {
	old := *q
	it := old[len(old)-1]
	*q = old[:len(old)-1]
	return it
}

// paint 는 git 의 paint_down_to_common(commit-reach.c)이 공통 조상
// 후보를 찾는 차례 — SPEC.md §10.2 의 1~4. 표시는 P1(a 에서 닿음)·
// P2(b 에서 닿음)·STALE(이미 찾은 후보의 조상). "넣을 때 STALE 이
// 아니었던" 커밋이 큐에 남아 있는 동안 돈다(git 의 max_nonstale).
// O(커밋 수 × log 커밋 수) 시간, O(커밋 수) 공간.
func paint(gitdir, a, b string) ([]string, error) {
	const p1, p2, stale = 1, 2, 4
	flags := map[string]int{}
	queued := map[string]bool{} // 큐에 있는 것 → 넣을 때 STALE 아니었나
	q := &paintQueue{}
	seq, live := 0, 0
	put := func(c string) error {
		if _, ok := queued[c]; ok {
			return nil // 이미 큐에 있으면 자리는 그대로
		}
		ci, err := parentsAndDate(gitdir, c)
		if err != nil {
			return err
		}
		queued[c] = flags[c]&stale == 0
		if queued[c] {
			live++
		}
		heap.Push(q, paintItem{c, ci.when, seq})
		seq++
		return nil
	}
	flags[a] = p1
	if err := put(a); err != nil {
		return nil, err
	}
	flags[b] |= p2
	if err := put(b); err != nil {
		return nil, err
	}
	var found []string
	isFound := map[string]bool{}
	for live > 0 {
		c := heap.Pop(q).(paintItem).oid
		if queued[c] {
			live--
		}
		delete(queued, c)
		f := flags[c] & (p1 | p2 | stale)
		if f == p1|p2 {
			if !isFound[c] {
				isFound[c] = true
				found = append(found, c)
			}
			f |= stale
		}
		ci, err := parentsAndDate(gitdir, c)
		if err != nil {
			return nil, err
		}
		for _, p := range ci.parents {
			if flags[p]&f == f {
				continue
			}
			flags[p] |= f
			if err := put(p); err != nil {
				return nil, err
			}
		}
	}
	var out []string
	for _, c := range found {
		if flags[c]&stale == 0 {
			out = append(out, c)
		}
	}
	return out, nil
}

// MergeBases 는 가장 좋은 공통 조상들(SPEC.md §10.2) — git 과 같은
// 차례로. paint 가 찾은 후보에서 다른 후보의 조상인 것을 차례를
// 지키며 빼고(git 의 remove_redundant), 커미터 날짜 내림차순으로 안정
// 정렬한다. 날짜가 같으면 찾은 차례가 남아, 인자 순서에 따라 답의
// 차례가 바뀐다 — git 도 그렇다. O(커밋 수 × 후보 수).
func MergeBases(gitdir, a, b string) ([]string, error) {
	cands, err := paint(gitdir, a, b)
	if err != nil {
		return nil, err
	}
	var best []string
	for _, c := range cands {
		redundant := false
		for _, o := range cands {
			if o == c {
				continue
			}
			if yes, err := IsAncestor(gitdir, c, o); err != nil {
				return nil, err
			} else if yes {
				redundant = true
				break
			}
		}
		if !redundant {
			best = append(best, c)
		}
	}
	when := map[string]int64{}
	for _, c := range best {
		ci, _ := parentsAndDate(gitdir, c) // paint 가 이미 읽었다
		when[c] = ci.when
	}
	sort.SliceStable(best, func(i, j int) bool {
		return when[best[i]] > when[best[j]]
	})
	return best, nil
}
