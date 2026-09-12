package compresslib

// 비트 writer/reader — SPEC §1.
//
// 우리 형식은 전부 MSB 먼저이고 DEFLATE 만 LSB 먼저다. 가장 자주
// 갈라지는 자리는 flush 의 채움이다 — **채움은 0** 이고, 쌓인 비트가
// 없으면 바이트를 내보내지 않는다.

type msbWriter struct {
	out []byte
	buf byte
	n   int
}

func (w *msbWriter) writeBit(bit int) {
	w.buf |= byte(bit&1) << (7 - w.n)
	w.n++
	if w.n == 8 {
		w.out = append(w.out, w.buf)
		w.buf = 0
		w.n = 0
	}
}

func (w *msbWriter) writeBits(v uint64, count int) {
	for i := count - 1; i >= 0; i-- {
		w.writeBit(int((v >> uint(i)) & 1))
	}
}

// MSB 스트림에서는 값도 부호도 같은 순서다. 이름만 따로 둔 것은
// LsbWriter 와 부르는 쪽 코드를 똑같이 만들기 위해서다.
func (w *msbWriter) writeCode(code uint64, count int) {
	w.writeBits(code, count)
}

func (w *msbWriter) bitPos() int { return len(w.out)*8 + w.n }

func (w *msbWriter) flush() {
	if w.n > 0 {
		w.out = append(w.out, w.buf)
		w.buf = 0
		w.n = 0
	}
}

type msbReader struct {
	src []byte
	pos int
	buf byte
	n   int
}

func (r *msbReader) readBit() int {
	if r.n == 0 {
		if r.pos >= len(r.src) {
			fail("비트 스트림이 바닥났다")
		}
		r.buf = r.src[r.pos]
		r.pos++
		r.n = 8
	}
	r.n--
	return int(r.buf>>uint(r.n)) & 1
}

func (r *msbReader) readBits(count int) uint64 {
	var v uint64
	for i := 0; i < count; i++ {
		v = v<<1 | uint64(r.readBit())
	}
	return v
}

func (r *msbReader) align() { r.n = 0 }

type lsbWriter struct {
	out []byte
	buf byte
	n   int
}

func (w *lsbWriter) writeBit(bit int) {
	w.buf |= byte(bit&1) << w.n
	w.n++
	if w.n == 8 {
		w.out = append(w.out, w.buf)
		w.buf = 0
		w.n = 0
	}
}

func (w *lsbWriter) writeBits(v uint64, count int) {
	for i := 0; i < count; i++ {
		w.writeBit(int((v >> uint(i)) & 1))
	}
}

// 허프만 부호만 같은 LSB 스트림에 높은 비트부터 넣는다 (RFC 1951).
func (w *lsbWriter) writeCode(code uint64, count int) {
	for i := count - 1; i >= 0; i-- {
		w.writeBit(int((code >> uint(i)) & 1))
	}
}

func (w *lsbWriter) bitPos() int { return len(w.out)*8 + w.n }

func (w *lsbWriter) flush() {
	if w.n > 0 {
		w.out = append(w.out, w.buf)
		w.buf = 0
		w.n = 0
	}
}

func (w *lsbWriter) align() { w.flush() }

type lsbReader struct {
	src []byte
	pos int
	buf byte
	n   int
}

func (r *lsbReader) readBit() int {
	if r.n == 0 {
		if r.pos >= len(r.src) {
			fail("비트 스트림이 바닥났다")
		}
		r.buf = r.src[r.pos]
		r.pos++
		r.n = 8
	}
	bit := int(r.buf & 1)
	r.buf >>= 1
	r.n--
	return bit
}

func (r *lsbReader) readBits(count int) uint64 {
	var v uint64
	for i := 0; i < count; i++ {
		v |= uint64(r.readBit()) << uint(i)
	}
	return v
}

func (r *lsbReader) align() { r.n = 0 }

// 골든 코덱 (SPEC §1.4). 앞의 0비트 셋이 요점 — 모든 바이트를 바이트
// 경계 밖으로 밀어내므로, 몰래 copy 하는 구현은 다른 파일을 낸다.
const bitioPadBits = 3

func BitioEncode(src []byte) (out []byte, err error) {
	defer guard(&err)
	var w msbWriter
	w.writeBits(0, bitioPadBits)
	for _, b := range src {
		w.writeBits(uint64(b), 8)
	}
	w.flush()
	return append(putVarint(nil, uint64(len(src))), w.out...), nil
}

func BitioDecode(src []byte) (out []byte, err error) {
	defer guard(&err)
	n, pos := getLength(src, 0)
	r := msbReader{src: src, pos: pos}
	r.readBits(bitioPadBits)
	result := make([]byte, 0, n)
	for i := 0; i < n; i++ {
		result = append(result, byte(r.readBits(8)))
	}
	return result, nil
}
