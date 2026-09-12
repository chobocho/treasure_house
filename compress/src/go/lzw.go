package compresslib

// LZ78 계열 — SPEC §7.
//
// **복호기는 부호기보다 항목 하나 뒤처진다.** 그래서 폭을 늘리는 조건이
// 부호기는 nextFree, 복호기는 nextFree+1 이다. 이 한 칸을 틀리면 사전
// 254번째 항목쯤부터 어긋난다 — 작은 시험은 전부 통과한다.

const (
	lzwClear     = 256
	lzwEOF       = 257
	lzwFirstFree = 258
	lzwMinWidth  = 9
	lzwMaxWidth  = 12
	lzwDictCap   = 1 << lzwMaxWidth
)

// 사전 열쇠 — (앞 부호, 다음 바이트). 트라이를 맵 하나로 눌러 담은
// 것이다.
type lzwKey struct {
	code int
	next byte
}

func LzwEncode(src []byte) (out []byte, err error) {
	defer guard(&err)
	if len(src) == 0 {
		return putVarint(nil, 0), nil
	}
	var w msbWriter
	table := make(map[lzwKey]int)
	nextFree := lzwFirstFree
	width := lzwMinWidth
	cur := -1
	for _, k := range src {
		if cur < 0 {
			cur = int(k)
			continue
		}
		if code, ok := table[lzwKey{cur, k}]; ok {
			cur = code
			continue
		}
		w.writeBits(uint64(cur), width)
		if nextFree == lzwDictCap {
			w.writeBits(lzwClear, width)
			table = make(map[lzwKey]int)
			nextFree = lzwFirstFree
			width = lzwMinWidth
		} else {
			table[lzwKey{cur, k}] = nextFree
			nextFree++
			// 폭 검사는 항목을 넣은 뒤에 — 다음 부호부터 넓어진다.
			if nextFree == 1<<uint(width) && width < lzwMaxWidth {
				width++
			}
		}
		cur = int(k)
	}
	if cur >= 0 {
		w.writeBits(uint64(cur), width)
	}
	w.writeBits(lzwEOF, width)
	w.flush()
	return append(putVarint(nil, uint64(len(src))), w.out...), nil
}

func LzwDecode(src []byte) (out []byte, err error) {
	defer guard(&err)
	n, pos := getLength(src, 0)
	if n == 0 {
		if pos != len(src) {
			fail("빈 입력인데 뒤에 바이트가 있다")
		}
		return []byte{}, nil
	}
	r := msbReader{src: src, pos: pos}
	result := make([]byte, 0, n)
	table := make([][]byte, lzwDictCap)
	nextFree := lzwFirstFree
	width := lzwMinWidth
	hasPrev := false
	var prev []byte
	for {
		code := int(r.readBits(width))
		if code == lzwEOF {
			break
		}
		if code == lzwClear {
			nextFree = lzwFirstFree
			width = lzwMinWidth
			hasPrev = false
			continue
		}
		var entry []byte
		switch {
		case !hasPrev:
			if code >= lzwClear {
				fail("첫 부호가 리터럴이 아니다: %d", code)
			}
			entry = []byte{byte(code)}
		case code < 256:
			entry = []byte{byte(code)}
		case code < nextFree:
			entry = table[code]
		case code == nextFree:
			// KwKwK — 부호기가 방금 만든 항목이다. 늘 prev + prev[0]
			// 이다.
			entry = append(append([]byte(nil), prev...), prev[0])
		default:
			fail("아직 없는 부호: %d", code)
		}
		result = append(result, entry...)
		if len(result) > n {
			fail("푼 길이가 헤더를 넘었다")
		}
		if hasPrev {
			added := append(append([]byte(nil), prev...), entry[0])
			table[nextFree] = added
			nextFree++
			// 복호기는 한 칸 뒤처져 있다. +1 이 그 보정이다.
			if nextFree+1 == 1<<uint(width) && width < lzwMaxWidth {
				width++
			}
		}
		prev = entry
		hasPrev = true
	}
	if len(result) != n {
		fail("푼 길이가 헤더와 다르다: %d != %d", len(result), n)
	}
	return result, nil
}
