package mygit

// 역사 걷기와 merge-base (SPEC.md §10).
//
// git 의 기본 log 차례는 "커미터 날짜가 늦은 것부터" 인데, 날짜가 같을
// 때의 규칙까지 정해져 있다 — 날짜 차례로 정렬된 목록에 새 커밋을
// 끼울 때 같은 날짜들 가운데 맨 뒤에 끼운다(git 의 commit_list_
// insert_by_date). 이 덱의 저장소는 모든 커밋의 날짜가 같게 만들어지
// 므로, 이 한 줄이 차례의 전부를 정한다.

import "sort"

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

// MergeBases 는 가장 좋은 공통 조상들(SPEC.md §10.2), 커미터 날짜
// 내림차순. 공통 조상 가운데 다른 공통 조상의 조상이 아닌 것만
// 남긴다. 작은 저장소를 위한 곧은 방법이다 — git 은 날짜로 칠하며
// 내려가는 더 빠른 길(paint_down_to_common)을 쓴다. O(커밋 수²) 최악.
func MergeBases(gitdir, a, b string) ([]string, error) {
	aa, err := ancestors(gitdir, a)
	if err != nil {
		return nil, err
	}
	bb, err := ancestors(gitdir, b)
	if err != nil {
		return nil, err
	}
	below := map[string]bool{}
	var common []string
	for c := range aa {
		if !bb[c] {
			continue
		}
		common = append(common, c)
		ci, _ := parentsAndDate(gitdir, c)
		for _, p := range ci.parents {
			anc, _ := ancestors(gitdir, p)
			for x := range anc {
				below[x] = true
			}
		}
	}
	var best []string
	for _, c := range common {
		if !below[c] {
			best = append(best, c)
		}
	}
	// 날짜가 같으면 이름 차례 — 맵 차례가 결과에 새지 않게
	sort.Slice(best, func(i, j int) bool {
		x, _ := parentsAndDate(gitdir, best[i])
		y, _ := parentsAndDate(gitdir, best[j])
		if x.when != y.when {
			return x.when > y.when
		}
		return best[i] < best[j]
	})
	return best, nil
}
