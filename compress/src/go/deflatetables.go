package compresslib

// DEFLATE 의 표들 — SPEC §10.3 (RFC 1951).
//
// 길이 부호 284 는 227..257 까지만 적을 수 있고, **길이 258 은 늘 285**
// 다. 284 + 여분 31 로도 258 이 되지만 진짜 부호기는 아무도 그러지
// 않는다.

const (
	dflMinMatch    = 3
	dflMaxMatch    = 258
	dflMaxDist     = 32768
	dflEndOfBlock  = 256
	dflLitlenSyms  = 286
	dflDistSyms    = 30
	dflClSyms      = 19
	dflClMaxLength = 7
	dflClRepeat    = 16
	dflClZeroShort = 17
	dflClZeroLong  = 18
)

var dflLengthExtra = [29]int{
	0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2,
	2, 3, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5, 0}

var dflLengthBase = [29]int{
	3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 15, 17, 19, 23,
	27, 31, 35, 43, 51, 59, 67, 83, 99, 115, 131, 163, 195, 227, 258}

var dflDistExtra = [30]int{
	0, 0, 0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6,
	6, 7, 7, 8, 8, 9, 9, 10, 10, 11, 11, 12, 12, 13, 13}

var dflDistBase = [30]int{
	1, 2, 3, 4, 5, 7, 9, 13, 17, 25,
	33, 49, 65, 97, 129, 193, 257, 385, 513, 769,
	1025, 1537, 2049, 3073, 4097, 6145, 8193, 12289, 16385, 24577}

// 자주 0 이 되는 것을 뒤로 몰아 HCLEN 으로 꼬리를 자를 수 있게 한 순서.
var dflClOrder = [19]int{16, 17, 18, 0, 8, 7, 9, 6, 10,
	5, 11, 4, 12, 3, 13, 2, 14, 1, 15}

var dflLengthCode = func() [dflMaxMatch + 1]int {
	var t [dflMaxMatch + 1]int
	for code, base := range dflLengthBase {
		top := base + 1<<uint(dflLengthExtra[code]) - 1
		if base == dflMaxMatch {
			top = dflMaxMatch
		}
		for ln := base; ln <= top && ln <= dflMaxMatch; ln++ {
			t[ln] = 257 + code
		}
	}
	t[dflMaxMatch] = 285 // 284 가 아니라 285 로 못 박는다
	return t
}()

func dflDistCode(dist int) int {
	for code := dflDistSyms - 1; code >= 0; code-- {
		if dist >= dflDistBase[code] {
			return code
		}
	}
	fail("거리가 1보다 작다: %d", dist)
	return 0
}

var dflFixedLitlen = func() []int {
	l := make([]int, 288)
	for s := range l {
		switch {
		case s < 144:
			l[s] = 8
		case s < 256:
			l[s] = 9
		case s < 280:
			l[s] = 7
		default:
			l[s] = 8
		}
	}
	return l
}()

var dflFixedDist = func() []int {
	l := make([]int, 32)
	for s := range l {
		l[s] = 5
	}
	return l
}()
