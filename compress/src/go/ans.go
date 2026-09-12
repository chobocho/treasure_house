package compresslib

// ANS — 비대칭 수 체계 — SPEC §13.
//
// rANS 는 **스택** 이다. 부호기가 입력을 뒤에서부터 밀어 넣고 복호기가
// 앞에서부터 꺼낸다. 상태 x 는 (x / f) * TOTAL 에서 2^31 에 닿으므로
// uint32 여야 한다 — int32 로는 모자란다.

const (
	ansTotalBits = 12
	ansTotal     = uint32(1) << ansTotalBits
	ansL         = uint32(1) << 23
	ansAlphabet  = 256
	// tANS 의 퍼뜨리기 걸음 (zstd 의 값). 홀수라서 2의 거듭제곱 칸을
	// 빠짐없이 한 번씩 돈다.
	ansSpreadStep = (ansTotal >> 1) + (ansTotal >> 3) + 3
)

// 빈도를 합이 정확히 ansTotal 이 되게 고친다 (SPEC §13.3).
// 남으면 가장 큰 기호에 한꺼번에, 모자라면 가장 큰 데서 되풀이해 뺀다.
// 동점이면 번호가 작은 쪽.
func ansNormalise(counts []uint64) []uint32 {
	var total uint64
	for _, c := range counts {
		total += c
	}
	f := make([]uint32, ansAlphabet)
	if total == 0 {
		return f
	}
	for s := 0; s < ansAlphabet; s++ {
		if counts[s] > 0 {
			v := counts[s] * uint64(ansTotal) / total
			if v < 1 {
				v = 1
			}
			f[s] = uint32(v)
		}
	}
	var sum int64
	for _, v := range f {
		sum += int64(v)
	}
	d := int64(ansTotal) - sum
	for d != 0 {
		best := 0
		for s := 1; s < ansAlphabet; s++ {
			if f[s] > f[best] {
				best = s
			}
		}
		if d > 0 {
			f[best] += uint32(d)
			d = 0
		} else {
			take := -d
			if take > int64(f[best])-1 {
				take = int64(f[best]) - 1
			}
			if take == 0 {
				fail("빈도를 TOTAL 에 못 맞춘다")
			}
			f[best] -= uint32(take)
			d += take
		}
	}
	return f
}

func ansCumulative(f []uint32) []uint32 {
	cum := make([]uint32, ansAlphabet)
	var total uint32
	for s := 0; s < ansAlphabet; s++ {
		cum[s] = total
		total += f[s]
	}
	return cum
}

func ansSlotSymbols(f, cum []uint32) []byte {
	slots := make([]byte, ansTotal)
	for s := 0; s < ansAlphabet; s++ {
		for i := cum[s]; i < cum[s]+f[s]; i++ {
			slots[i] = byte(s)
		}
	}
	return slots
}

// tANS 의 상태표 (SPEC §13.6). 골든에는 안 들어가고 12부가 쓴다.
func ansTansTable(f []uint32) []byte {
	table := make([]byte, ansTotal)
	var pos uint32
	for s := 0; s < ansAlphabet; s++ {
		for i := uint32(0); i < f[s]; i++ {
			table[pos] = byte(s)
			pos = (pos + ansSpreadStep) & (ansTotal - 1)
		}
	}
	return table
}

func AnsEncode(src []byte) (out []byte, err error) {
	defer guard(&err)
	if len(src) == 0 {
		return putVarint(nil, 0), nil
	}
	counts := make([]uint64, ansAlphabet)
	for _, b := range src {
		counts[b]++
	}
	f := ansNormalise(counts)
	cum := ansCumulative(f)

	var body []byte
	x := ansL
	// 뒤에서부터 민다. rANS 는 스택이라 마지막에 넣은 것이 먼저 나온다.
	for i := len(src) - 1; i >= 0; i-- {
		s := src[i]
		fs := f[s]
		xmax := ((ansL >> ansTotalBits) << 8) * fs
		for x >= xmax {
			body = append(body, byte(x))
			x >>= 8
		}
		x = (x/fs)*ansTotal + x%fs + cum[s]
	}
	for i := 0; i < 4; i++ {
		body = append(body, byte(x>>(8*uint(i))))
	}
	for i, j := 0, len(body)-1; i < j; i, j = i+1, j-1 {
		body[i], body[j] = body[j], body[i]
	}

	result := putVarint(nil, uint64(len(src)))
	for s := 0; s < ansAlphabet; s++ {
		result = putVarint(result, uint64(f[s]))
	}
	return append(result, body...), nil
}

func AnsDecode(src []byte) (out []byte, err error) {
	defer guard(&err)
	n, pos := getLength(src, 0)
	if n == 0 {
		if pos != len(src) {
			fail("빈 입력인데 뒤에 바이트가 있다")
		}
		return []byte{}, nil
	}
	f := make([]uint32, ansAlphabet)
	var sum uint64
	for s := 0; s < ansAlphabet; s++ {
		var v uint64
		v, pos = getVarint(src, pos)
		if v > uint64(ansTotal) {
			fail("빈도가 TOTAL 을 넘는다")
		}
		f[s] = uint32(v)
		sum += v
	}
	if sum != uint64(ansTotal) {
		fail("빈도의 합이 %d 가 아니다", ansTotal)
	}
	cum := ansCumulative(f)
	slots := ansSlotSymbols(f, cum)

	if len(src)-pos < 4 {
		fail("rANS 스트림이 너무 짧다")
	}
	var x uint32
	for i := 0; i < 4; i++ {
		x = x<<8 | uint32(src[pos+i])
	}
	at := pos + 4
	result := make([]byte, 0, n)
	mask := ansTotal - 1
	for k := 0; k < n; k++ {
		slot := x & mask
		s := slots[slot]
		result = append(result, s)
		x = f[s]*(x>>ansTotalBits) + slot - cum[s]
		for x < ansL {
			if at >= len(src) {
				fail("rANS 스트림이 모자란다")
			}
			x = x<<8 | uint32(src[at])
			at++
		}
	}
	if at != len(src) {
		fail("뒤에 남은 바이트가 있다")
	}
	return result, nil
}
