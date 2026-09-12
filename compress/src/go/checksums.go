package compresslib

// Adler-32 과 CRC-32 — SPEC §10.8.
//
// 압축과는 상관없는 물건인데 압축 컨테이너마다 붙어 있다. 압축은 한
// 비트만 어긋나도 전혀 다른 것이 풀려 나온다. 원본이 맞는지 볼 방법이
// 없으면 "풀렸다" 와 "제대로 풀렸다" 를 구별할 수 없다.
//
// 표는 다항식에서 만든다. 숫자 256개를 다섯 언어에 옮겨 적으면 틀린다.

const (
	adlerMod = 65521
	// b 가 32비트를 넘기 전에 나눠야 하는 폭 (zlib 의 NMAX)
	adlerNmax = 5552
	crcPoly   = 0xEDB88320
)

func adler32(data []byte) uint32 {
	var a, b uint32 = 1, 0
	for i := 0; i < len(data); i += adlerNmax {
		end := i + adlerNmax
		if end > len(data) {
			end = len(data)
		}
		for _, c := range data[i:end] {
			a += uint32(c)
			b += a
		}
		a %= adlerMod
		b %= adlerMod
	}
	return b<<16 | a
}

var crcTable = func() [256]uint32 {
	var t [256]uint32
	for i := 0; i < 256; i++ {
		c := uint32(i)
		for k := 0; k < 8; k++ {
			if c&1 != 0 {
				c = c>>1 ^ crcPoly
			} else {
				c >>= 1
			}
		}
		t[i] = c
	}
	return t
}()

func crc32of(data []byte) uint32 {
	c := uint32(0xFFFFFFFF)
	for _, b := range data {
		c = crcTable[(c^uint32(b))&0xFF] ^ c>>8
	}
	return c ^ 0xFFFFFFFF
}
