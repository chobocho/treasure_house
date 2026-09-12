package compresslib

// LZ4 — SPEC §14.
//
// LZ77 인데 **엔트로피 부호가 아예 없다.** 리터럴과 일치를 바이트로
// 그냥 적는다. DEFLATE 보다 덜 줄고 몇 배 빨리 풀린다.
//
// 꼬리 규칙 둘: 마지막 5바이트는 반드시 리터럴, 일치는 끝에서 12바이트
// 안쪽에서 시작 금지. 지키지 않으면 진짜 lz4 가 거절한다.

const (
	lz4MinMatch     = 4
	lz4LastLiterals = 5
	lz4MfLimit      = 12
	lz4HashLog      = 12
	lz4HashSize     = 1 << lz4HashLog
	lz4HashMul      = 2654435761
	lz4MaxOffset    = 65535
)

func lz4PutLsic(out []byte, v int) []byte {
	for v >= 255 {
		out = append(out, 255)
		v -= 255
	}
	return append(out, byte(v))
}

// 고리를 묶는 것은 입력 자신이다 — 이어짐 바이트가 남은 것보다 많을 수
// 없다. 고정 상한은 솔깃하고 틀린다 (SPEC §14.3).
func lz4GetLsic(src []byte, pos int) (int, int) {
	total := 0
	for pos < len(src) {
		b := int(src[pos])
		pos++
		total += b
		if b != 255 {
			if int64(total) > varintMaxLength {
				fail("LSIC 값이 너무 크다")
			}
			return total, pos
		}
	}
	fail("LSIC 가 잘렸다")
	return 0, 0
}

func lz4Hash4(s []byte, i int) int {
	v := uint32(s[i]) | uint32(s[i+1])<<8 | uint32(s[i+2])<<16 |
		uint32(s[i+3])<<24
	return int((v * lz4HashMul) >> (32 - lz4HashLog))
}

func lz4Same4(s []byte, a, b int) bool {
	return s[a] == s[b] && s[a+1] == s[b+1] && s[a+2] == s[b+2] &&
		s[a+3] == s[b+3]
}

// 시퀀스 하나. hasMatch 가 거짓이면 마지막(리터럴만) 시퀀스다.
func lz4Emit(out, src []byte, from, to int, hasMatch bool,
	offset, length int) []byte {
	litLen := to - from
	tokenLit := litLen
	if tokenLit > 15 {
		tokenLit = 15
	}
	if !hasMatch {
		out = append(out, byte(tokenLit<<4))
		if litLen >= 15 {
			out = lz4PutLsic(out, litLen-15)
		}
		return append(out, src[from:to]...)
	}
	mlCode := length - lz4MinMatch
	tokenMl := mlCode
	if tokenMl > 15 {
		tokenMl = 15
	}
	out = append(out, byte(tokenLit<<4|tokenMl))
	if litLen >= 15 {
		out = lz4PutLsic(out, litLen-15)
	}
	out = append(out, src[from:to]...)
	out = append(out, byte(offset&0xFF), byte(offset>>8))
	if mlCode >= 15 {
		out = lz4PutLsic(out, mlCode-15)
	}
	return out
}

func lz4CompressBlock(src []byte) []byte {
	n := len(src)
	var out []byte
	if n < lz4MfLimit+1 {
		return lz4Emit(out, src, 0, n, false, 0, 0)
	}
	table := make([]int, lz4HashSize)
	for i := range table {
		table[i] = -1
	}
	ip, anchor := 0, 0
	for ip <= n-lz4MfLimit {
		h := lz4Hash4(src, ip)
		ref := table[h]
		table[h] = ip
		if ref >= 0 && ip-ref <= lz4MaxOffset &&
			lz4Same4(src, ref, ip) {
			ml := lz4MinMatch
			limit := n - lz4LastLiterals
			for ip+ml < limit && src[ref+ml] == src[ip+ml] {
				ml++
			}
			out = lz4Emit(out, src, anchor, ip, true, ip-ref, ml)
			ip += ml
			anchor = ip
		} else {
			ip++
		}
	}
	return lz4Emit(out, src, anchor, n, false, 0, 0)
}

func lz4DecompressBlock(block []byte, check bool, want int) []byte {
	var out []byte
	pos, n := 0, len(block)
	for pos < n {
		token := int(block[pos])
		pos++
		litLen := token >> 4
		if litLen == 15 {
			var extra int
			extra, pos = lz4GetLsic(block, pos)
			litLen += extra
		}
		if pos+litLen > n {
			fail("리터럴이 잘렸다")
		}
		out = append(out, block[pos:pos+litLen]...)
		pos += litLen
		if pos == n {
			break // 마지막 시퀀스는 리터럴뿐이다
		}
		if pos+2 > n {
			fail("거리가 잘렸다")
		}
		offset := int(block[pos]) | int(block[pos+1])<<8
		pos += 2
		length := token & 15
		if length == 15 {
			var extra int
			extra, pos = lz4GetLsic(block, pos)
			length += extra
		}
		length += lz4MinMatch
		if offset == 0 {
			fail("거리 0 은 없다")
		}
		if offset > len(out) {
			fail("거리 %d 가 지금까지 낸 것보다 멀다", offset)
		}
		start := len(out) - offset
		// 한 바이트씩 앞으로. 거리 1 짜리 긴 일치가 여기 기댄다.
		for j := 0; j < length; j++ {
			out = append(out, out[start+j])
		}
	}
	if check && len(out) != want {
		fail("푼 길이가 헤더와 다르다: %d != %d", len(out), want)
	}
	return out
}

func Lz4blockEncode(src []byte) (out []byte, err error) {
	defer guard(&err)
	if len(src) == 0 {
		return putVarint(nil, 0), nil
	}
	head := putVarint(nil, uint64(len(src)))
	return append(head, lz4CompressBlock(src)...), nil
}

func Lz4blockDecode(src []byte) (out []byte, err error) {
	defer guard(&err)
	n, pos := getLength(src, 0)
	if n == 0 {
		if pos != len(src) {
			fail("빈 입력인데 뒤에 바이트가 있다")
		}
		return []byte{}, nil
	}
	return lz4DecompressBlock(src[pos:], true, n), nil
}

// 진짜 lz4 명령이 쓰는 프레임을 푼다 (§14.6). 쓰지는 않는다.
// 내용 검사합(xxHash)은 건너뛴다 — 이유는 명세에 적어 뒀다.
func Lz4FrameDecode(src []byte) (out []byte, err error) {
	defer guard(&err)
	if len(src) < 7 || src[0] != 0x04 || src[1] != 0x22 ||
		src[2] != 0x4D || src[3] != 0x18 {
		fail("lz4 프레임 매직이 아니다")
	}
	flg := src[4]
	if flg>>6 != 1 {
		fail("모르는 프레임 판: %d", flg>>6)
	}
	blockChecksum := flg&0x10 != 0
	contentSize := flg&0x08 != 0
	contentChecksum := flg&0x04 != 0
	dictID := flg&0x01 != 0
	pos := 6
	if contentSize {
		pos += 8
	}
	if dictID {
		pos += 4
	}
	pos++ // 머리 검사 바이트(HC)
	var result []byte
	for {
		if pos+4 > len(src) {
			fail("블록 크기가 잘렸다")
		}
		size := uint32(src[pos]) | uint32(src[pos+1])<<8 |
			uint32(src[pos+2])<<16 | uint32(src[pos+3])<<24
		pos += 4
		if size == 0 {
			break
		}
		stored := size&0x80000000 != 0
		size &= 0x7FFFFFFF
		if pos+int(size) > len(src) {
			fail("블록이 잘렸다")
		}
		chunk := src[pos : pos+int(size)]
		pos += int(size)
		if blockChecksum {
			pos += 4
		}
		if stored {
			result = append(result, chunk...)
		} else {
			part := lz4DecompressBlock(chunk, false, 0)
			result = append(result, part...)
		}
	}
	if contentChecksum {
		pos += 4
	}
	return result, nil
}
