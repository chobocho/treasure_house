package compresslib

// 버로우즈–휠러 변환 — SPEC §9.
//
// 배가 늘리기 정렬. 키를 rank[i]*(m+1) + rank[i+k] 로 눌러 담는데, **첫
// 회의 rank 를 바이트 값 그대로 쓰면 안 된다** — 곱수 m+1 이 255 보다
// 작아져 자리가 겹친다. 0..(서로 다른 값 수-1) 로 먼저 압축한다. 같은
// 회전이 여럿이면 순서는 시작 위치 오름차순 — 안정 정렬이 필요하다.

import "sort"

const (
	bwtBlock    = 1 << 16
	bwtAlphabet = 256
)

func bwtTransformBlock(block []byte) ([]byte, uint32) {
	m := len(block)
	if m == 0 {
		return nil, 0
	}
	var order [bwtAlphabet]int
	for _, c := range block {
		order[c] = 1
	}
	next := 0
	for i := 0; i < bwtAlphabet; i++ {
		if order[i] > 0 {
			order[i] = next
			next++
		}
	}
	rank := make([]uint64, m)
	for i, c := range block {
		rank[i] = uint64(order[c])
	}
	sa := make([]int, m)
	for i := range sa {
		sa[i] = i
	}
	keys := make([]uint64, m)
	newRank := make([]uint64, m)
	mul := uint64(m) + 1
	for k := 1; ; k *= 2 {
		for i := 0; i < m; i++ {
			keys[i] = rank[i]*mul + rank[(i+k)%m]
		}
		sort.SliceStable(sa, func(a, b int) bool {
			return keys[sa[a]] < keys[sa[b]]
		})
		var r uint64
		newRank[sa[0]] = 0
		for j := 1; j < m; j++ {
			if keys[sa[j]] != keys[sa[j-1]] {
				r++
			}
			newRank[sa[j]] = r
		}
		copy(rank, newRank)
		if r == uint64(m-1) || k >= m {
			break
		}
	}
	l := make([]byte, m)
	var primary uint32
	for j, i := range sa {
		l[j] = block[(i+m-1)%m]
		if i == 0 {
			primary = uint32(j)
		}
	}
	return l, primary
}

func bwtInverseBlock(l []byte, primary uint32) []byte {
	m := len(l)
	if m == 0 {
		return nil
	}
	if int(primary) >= m {
		fail("primary 가 범위 밖이다: %d", primary)
	}
	var count, first, occ [bwtAlphabet]uint32
	for _, c := range l {
		count[c]++
	}
	var total uint32
	for c := 0; c < bwtAlphabet; c++ {
		first[c] = total
		total += count[c]
	}
	// nxt 는 LF 의 역치환이다. LF 로 걸으면 원문이 거꾸로 나오고,
	// nxt 로 걸으면 바로 나온다.
	nxt := make([]uint32, m)
	for i, c := range l {
		nxt[first[c]+occ[c]] = uint32(i)
		occ[c]++
	}
	out := make([]byte, 0, m)
	i := primary
	for step := 0; step < m; step++ {
		i = nxt[i]
		out = append(out, l[i])
	}
	return out
}

func BwtEncode(src []byte) (out []byte, err error) {
	defer guard(&err)
	result := putVarint(nil, uint64(len(src)))
	for off := 0; off < len(src); off += bwtBlock {
		end := off + bwtBlock
		if end > len(src) {
			end = len(src)
		}
		l, primary := bwtTransformBlock(src[off:end])
		result = append(result, byte(primary), byte(primary>>8),
			byte(primary>>16), byte(primary>>24))
		result = append(result, l...)
	}
	return result, nil
}

func BwtDecode(src []byte) (out []byte, err error) {
	defer guard(&err)
	n, pos := getLength(src, 0)
	result := make([]byte, 0, n)
	left := n
	for left > 0 {
		m := bwtBlock
		if left < m {
			m = left
		}
		if pos+4+m > len(src) {
			fail("블록이 잘렸다")
		}
		primary := uint32(src[pos]) | uint32(src[pos+1])<<8 |
			uint32(src[pos+2])<<16 | uint32(src[pos+3])<<24
		pos += 4
		part := bwtInverseBlock(src[pos:pos+m], primary)
		result = append(result, part...)
		pos += m
		left -= m
	}
	if pos != len(src) {
		fail("뒤에 남은 바이트가 있다")
	}
	return result, nil
}
