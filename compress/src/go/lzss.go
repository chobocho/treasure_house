package compresslib

// LZ77 계열 — SPEC §6.
//
// 사슬 배열을 **절대 위치로** 잡는다. zlib 은 창 크기 배열에 감아
// 넣어서 pos-32768 자리를 pos 가 덮어쓰고, 그래서 실효 최대 거리가
// 32506 이다. 후보 교체 비교는 > 다. >= 로 쓰면 같은 길이에서 먼 쪽을
// 골라, 정상 복호되는 **다른** 파일이 나온다.

const (
	lzWindow     = 32768
	lzMinMatch   = 3
	lzMaxMatch   = 258
	lzHashBits   = 15
	lzHashSize   = 1 << lzHashBits
	lzChainLimit = 32
	lzNil        = -1
)

type lzToken struct {
	isMatch bool
	literal byte
	length  int
	dist    int
}

func lzHash3(s []byte, i int) int {
	h := int(s[i])<<10 ^ int(s[i+1])<<5 ^ int(s[i+2])
	return h & (lzHashSize - 1)
}

func lzssFindTokens(src []byte) []lzToken {
	n := len(src)
	head := make([]int32, lzHashSize)
	for i := range head {
		head[i] = lzNil
	}
	prev := make([]int32, max(n, 1))
	for i := range prev {
		prev[i] = lzNil
	}
	var tokens []lzToken
	i := 0
	for i < n {
		bestLen, bestDist := 0, 0
		if i+lzMinMatch <= n {
			limit := lzMaxMatch
			if n-i < limit {
				limit = n - i
			}
			cand := head[lzHash3(src, i)]
			probes := 0
			for cand != lzNil && probes < lzChainLimit {
				c := int(cand)
				dist := i - c
				if dist > lzWindow {
					break
				}
				ln := 0
				for ln < limit && src[c+ln] == src[i+ln] {
					ln++
				}
				if ln > bestLen {
					bestLen, bestDist = ln, dist
					if ln == limit {
						break
					}
				}
				cand = prev[c]
				probes++
			}
		}
		if bestLen >= lzMinMatch {
			for k := 0; k < bestLen; k++ {
				p := i + k
				if p+lzMinMatch <= n {
					h := lzHash3(src, p)
					prev[p] = head[h]
					head[h] = int32(p)
				}
			}
			tokens = append(tokens, lzToken{true, 0, bestLen, bestDist})
			i += bestLen
		} else {
			if i+lzMinMatch <= n {
				h := lzHash3(src, i)
				prev[i] = head[h]
				head[h] = int32(i)
			}
			tokens = append(tokens, lzToken{false, src[i], 0, 0})
			i++
		}
	}
	return tokens
}

func LzssEncode(src []byte) (out []byte, err error) {
	defer guard(&err)
	tokens := lzssFindTokens(src)
	result := putVarint(nil, uint64(len(src)))
	for base := 0; base < len(tokens); base += 8 {
		end := base + 8
		if end > len(tokens) {
			end = len(tokens)
		}
		flag := byte(0)
		for k := base; k < end; k++ {
			if tokens[k].isMatch {
				flag |= 1 << uint(7-(k-base))
			}
		}
		result = append(result, flag)
		for k := base; k < end; k++ {
			t := tokens[k]
			if t.isMatch {
				d := t.dist - 1
				result = append(result, byte(t.length-lzMinMatch),
					byte(d&0xFF), byte(d>>8))
			} else {
				result = append(result, t.literal)
			}
		}
	}
	return result, nil
}

func LzssDecode(src []byte) (out []byte, err error) {
	defer guard(&err)
	n, pos := getLength(src, 0)
	end := len(src)
	result := make([]byte, 0, n)
	for len(result) < n {
		if pos >= end {
			fail("플래그 바이트가 없다")
		}
		flag := src[pos]
		pos++
		for k := 0; k < 8 && len(result) < n; k++ {
			if flag&(1<<uint(7-k)) != 0 {
				if pos+3 > end {
					fail("일치 토큰이 잘렸다")
				}
				ln := int(src[pos]) + lzMinMatch
				dist := int(src[pos+1]) | int(src[pos+2])<<8
				dist++
				pos += 3
				if dist > len(result) {
					fail("거리 %d 가 낸 것보다 멀다", dist)
				}
				start := len(result) - dist
				// 한 바이트씩 앞으로. 거리 1 짜리 긴 일치가 여기 기댄다
				// — copy 로 한 번에 옮기면 틀린다.
				for j := 0; j < ln; j++ {
					result = append(result, result[start+j])
				}
			} else {
				if pos >= end {
					fail("리터럴이 잘렸다")
				}
				result = append(result, src[pos])
				pos++
			}
		}
	}
	if len(result) != n {
		fail("푼 길이가 헤더와 다르다")
	}
	if pos != end {
		fail("뒤에 남은 바이트가 있다")
	}
	return result, nil
}
