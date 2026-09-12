package compresslib

// LEB128 가변 길이 정수 — SPEC §2.1.
//
// 명세에서는 intcode 의 일부지만 파일을 갈랐다. 모든 코덱 헤더가 varint
// 로 시작하는데 intcode 는 비트 스트림을 쓰고 bitio 의 골든 코덱은 다시
// varint 를 쓴다. 다섯 언어 모두 같은 이유로 같게 갈라 뒀다.

const (
	varintMaxBytes = 10
	// 길이 칸의 상한. 손상된 헤더가 불가능한 할당을 요구하지 못하게
	// 막는다.
	varintMaxLength = 0xFFFFFFFF
)

func putVarint(dst []byte, value uint64) []byte {
	for {
		b := byte(value & 0x7F)
		value >>= 7
		if value != 0 {
			dst = append(dst, b|0x80)
		} else {
			return append(dst, b)
		}
	}
}

func getVarint(src []byte, pos int) (uint64, int) {
	var value uint64
	shift := uint(0)
	for i := 0; i < varintMaxBytes; i++ {
		if pos >= len(src) {
			fail("varint 가 잘렸다")
		}
		b := src[pos]
		pos++
		// 마지막 바이트에서 7비트를 다 쓰면 64비트를 넘는다.
		if i == varintMaxBytes-1 && b&0x7F > 1 {
			fail("varint 가 64비트를 넘는다")
		}
		value |= uint64(b&0x7F) << shift
		if b&0x80 == 0 {
			return value, pos
		}
		shift += 7
	}
	fail("varint 가 %d바이트를 넘는다", varintMaxBytes)
	return 0, 0
}

func getLength(src []byte, pos int) (int, int) {
	v, next := getVarint(src, pos)
	if v > varintMaxLength {
		fail("길이 칸이 너무 크다: %d", v)
	}
	return int(v), next
}
