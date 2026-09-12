package compresslib

// 런 길이 부호 — SPEC §3.
//
// 정한 값 셋이 출력 바이트를 바꾼다: 문턱 3, 런 상한 128, 리터럴 상한
// 128. 리터럴 묶음을 min(j+r, i+128) 로 자르는 것이 특히 중요하다 — 안
// 자르면 129바이트 묶음이 나오는데, 제어 바이트에 안 들어가는 길이라 못
// 푼다.

const (
	rleRunMin   = 3
	rleRunMax   = 128
	rleLitMax   = 128
	rleReserved = 128
)

func runAt(src []byte, i, limit int) int {
	b := src[i]
	j := i + 1
	end := i + limit
	if end > len(src) {
		end = len(src)
	}
	for j < end && src[j] == b {
		j++
	}
	return j - i
}

func rlePack(src, out []byte) []byte {
	i, n := 0, len(src)
	for i < n {
		run := runAt(src, i, rleRunMax)
		if run >= rleRunMin {
			out = append(out, byte(257-run), src[i])
			i += run
			continue
		}
		j := i
		for j < n && j-i < rleLitMax {
			r := runAt(src, j, rleRunMax)
			if r >= rleRunMin {
				break
			}
			if j+r > i+rleLitMax {
				j = i + rleLitMax
			} else {
				j += r
			}
		}
		out = append(out, byte(j-i-1))
		out = append(out, src[i:j]...)
		i = j
	}
	return out
}

func rleUnpack(src []byte, pos, want int) ([]byte, int) {
	out := make([]byte, 0, want)
	n := len(src)
	for len(out) < want {
		if pos >= n {
			fail("PackBits 가 잘렸다")
		}
		c := src[pos]
		pos++
		switch {
		case c == rleReserved:
			fail("제어 128 은 쓰지 않는다")
		case c < rleReserved:
			k := int(c) + 1
			if pos+k > n {
				fail("리터럴 묶음이 잘렸다")
			}
			out = append(out, src[pos:pos+k]...)
			pos += k
		default:
			k := 257 - int(c)
			if pos >= n {
				fail("런 묶음이 잘렸다")
			}
			for j := 0; j < k; j++ {
				out = append(out, src[pos])
			}
			pos++
		}
	}
	if len(out) != want {
		fail("푼 길이가 헤더와 다르다")
	}
	return out, pos
}

func RleEncode(src []byte) (out []byte, err error) {
	defer guard(&err)
	return rlePack(src, putVarint(nil, uint64(len(src)))), nil
}

func RleDecode(src []byte) (out []byte, err error) {
	defer guard(&err)
	n, pos := getLength(src, 0)
	result, pos := rleUnpack(src, pos, n)
	if pos != len(src) {
		fail("뒤에 남은 바이트가 있다")
	}
	return result, nil
}

// 0런 부호 (SPEC §3.2) — bzip2 의 RUNA/RUNB. 13번 모듈이 쓴다.
const (
	runA = 0
	runB = 1
)

func zeroRunEncode(syms []int) []int {
	var out []int
	i, n := 0, len(syms)
	for i < n {
		if syms[i] != 0 {
			out = append(out, syms[i]+1)
			i++
			continue
		}
		j := i
		for j < n && syms[j] == 0 {
			j++
		}
		length := uint64(j-i) + 1
		for length > 1 {
			if length&1 == 1 {
				out = append(out, runB)
			} else {
				out = append(out, runA)
			}
			length >>= 1
		}
		i = j
	}
	return out
}

func zeroRunDecode(syms []int) []int {
	var out []int
	i, n := 0, len(syms)
	for i < n {
		if syms[i] > 1 {
			out = append(out, syms[i]-1)
			i++
			continue
		}
		var run, weight uint64 = 0, 1
		for i < n && syms[i] <= 1 {
			run += uint64(syms[i]+1) * weight
			weight <<= 1
			i++
		}
		for j := uint64(0); j < run; j++ {
			out = append(out, 0)
		}
	}
	return out
}
