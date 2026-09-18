package mygit

// SHA-1 을 손으로 (SPEC.md §2 · FIPS 180-4).
//
// git 의 모든 객체 이름이 이 함수의 출력이다. crypto/sha1 을 부르면 한
// 줄이지만 그러면 "40글자 이름이 어디서 오나" 가 가려진다. 한 블록
// (64바이트) = 80라운드, 전체 O(n) 시간, O(1) 추가 공간. Go 의 uint32
// 는 저절로 2³² 에서 넘치므로 & 가 필요 없다 — Python 과 다른 점이다.

import (
	"encoding/binary"
	"encoding/hex"
	"math/bits"
)

var sha1Init = [5]uint32{0x67452301, 0xefcdab89, 0x98badcfe,
	0x10325476, 0xc3d2e1f0}

// Sha1 은 스트리밍 SHA-1 이다. 인덱스와 팩의 끝 체크섬을 읽어 가며
// 셀 때 쓴다.
type Sha1 struct {
	h   [5]uint32
	buf []byte
	n   uint64
}

func NewSha1() *Sha1 { return &Sha1{h: sha1Init} }

func compress1(h *[5]uint32, block []byte) {
	var w [80]uint32
	for t := 0; t < 16; t++ {
		w[t] = binary.BigEndian.Uint32(block[4*t:])
	}
	for t := 16; t < 80; t++ {
		w[t] = bits.RotateLeft32(w[t-3]^w[t-8]^w[t-14]^w[t-16], 1)
	}
	a, b, c, d, e := h[0], h[1], h[2], h[3], h[4]
	for t := 0; t < 80; t++ {
		var f, k uint32
		switch {
		case t < 20:
			f, k = (b&c)|(^b&d), 0x5a827999
		case t < 40:
			f, k = b^c^d, 0x6ed9eba1
		case t < 60:
			f, k = (b&c)|(b&d)|(c&d), 0x8f1bbcdc
		default:
			f, k = b^c^d, 0xca62c1d6
		}
		tmp := bits.RotateLeft32(a, 5) + f + e + k + w[t]
		a, b, c, d, e = tmp, a, bits.RotateLeft32(b, 30), c, d
	}
	h[0] += a
	h[1] += b
	h[2] += c
	h[3] += d
	h[4] += e
}

func (s *Sha1) Update(p []byte) {
	s.n += uint64(len(p))
	s.buf = append(s.buf, p...)
	whole := len(s.buf) - len(s.buf)%64
	for k := 0; k < whole; k += 64 {
		compress1(&s.h, s.buf[k:k+64])
	}
	s.buf = append([]byte(nil), s.buf[whole:]...)
}

// Digest 는 덧붙임(0x80 · 0 들 · 비트 길이 빅 엔디언 64비트)을 사본에서
// 마무리한다 — 두 번 불러도 같다. 55바이트까지는 한 블록, 56부터 둘.
func (s *Sha1) Digest() [20]byte {
	h := s.h
	tail := append(append([]byte(nil), s.buf...), 0x80)
	for len(tail)%64 != 56 {
		tail = append(tail, 0)
	}
	tail = binary.BigEndian.AppendUint64(tail, s.n*8)
	for k := 0; k < len(tail); k += 64 {
		compress1(&h, tail[k:k+64])
	}
	var out [20]byte
	for i, v := range h {
		binary.BigEndian.PutUint32(out[4*i:], v)
	}
	return out
}

// Sum1 은 바이트열의 SHA-1, 20바이트.
func Sum1(data []byte) [20]byte {
	s := NewSha1()
	s.Update(data)
	return s.Digest()
}

// Sum1Hex 는 소문자 16진 40글자 — git 이 찍는 객체 이름의 꼴.
func Sum1Hex(data []byte) string {
	d := Sum1(data)
	return hex.EncodeToString(d[:])
}
