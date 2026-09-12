package compresslib

// 이진 레인지 코더 — SPEC §8. LZMA 의 것 그대로.
//
// Go 는 부호 없는 정수가 제대로 있어서 다섯 언어 중 가장 손이 덜 간다.
// low 가 2^33 까지 가므로 uint64, 나머지는 uint32 다.

const (
	probBits  = 11
	probTotal = 1 << probBits
	probInit  = probTotal / 2
	moveBits  = 5
	rcTop     = 1 << 24
)

type rcEncoder struct {
	low       uint64 // 최대 2^33 — 32비트가 아니다
	rng       uint32
	cache     byte
	cacheSize uint64
	out       []byte
}

func newRcEncoder() *rcEncoder {
	return &rcEncoder{rng: 0xFFFFFFFF, cacheSize: 1}
}

// 위 바이트 하나를 확정해 내보낸다. 캐리는 앞으로 전파한다.
func (e *rcEncoder) shiftLow() {
	if e.low>>32 != 0 || e.low < 0xFF000000 {
		carry := byte(e.low >> 32)
		temp := e.cache
		for {
			e.out = append(e.out, temp+carry)
			temp = 0xFF
			e.cacheSize--
			if e.cacheSize == 0 {
				break
			}
		}
		e.cache = byte(e.low >> 24)
	}
	e.cacheSize++
	e.low = e.low << 8 & 0xFFFFFFFF
}

func (e *rcEncoder) encodeBit(probs []uint16, i int, bit int) {
	bound := (e.rng >> probBits) * uint32(probs[i])
	if bit == 0 {
		e.rng = bound
		probs[i] += uint16((probTotal - uint32(probs[i])) >> moveBits)
	} else {
		e.low += uint64(bound)
		e.rng -= bound
		probs[i] -= probs[i] >> moveBits
	}
	for e.rng < rcTop {
		e.rng <<= 8
		e.shiftLow()
	}
}

func (e *rcEncoder) flush() {
	for i := 0; i < 5; i++ {
		e.shiftLow()
	}
}

type rcDecoder struct {
	src []byte
	pos int
	rng uint32
	cod uint32
}

func newRcDecoder(src []byte, pos int) *rcDecoder {
	d := &rcDecoder{src: src, pos: pos, rng: 0xFFFFFFFF}
	if pos >= len(src) {
		fail("레인지 코더 스트림이 비었다")
	}
	if src[pos] != 0 {
		fail("첫 바이트가 0 이 아니다: %d", src[pos])
	}
	d.pos++
	for i := 0; i < 4; i++ {
		d.cod = d.cod<<8 | uint32(d.nextByte())
	}
	return d
}

func (d *rcDecoder) nextByte() byte {
	// 잘 만들어진 스트림도 마지막 판정에서 한 바이트쯤 더 읽는다.
	if d.pos < len(d.src) {
		b := d.src[d.pos]
		d.pos++
		return b
	}
	d.pos++
	if d.pos > len(d.src)+5 {
		fail("스트림 끝을 너무 많이 넘었다")
	}
	return 0
}

func (d *rcDecoder) decodeBit(probs []uint16, i int) int {
	bound := (d.rng >> probBits) * uint32(probs[i])
	var bit int
	if d.cod < bound {
		d.rng = bound
		probs[i] += uint16((probTotal - uint32(probs[i])) >> moveBits)
		bit = 0
	} else {
		d.cod -= bound
		d.rng -= bound
		probs[i] -= probs[i] >> moveBits
		bit = 1
	}
	for d.rng < rcTop {
		d.rng <<= 8
		d.cod = d.cod<<8 | uint32(d.nextByte())
	}
	return bit
}

// 0차 적응 바이트 모델. 문맥은 1 에서 시작해 여덟 번 만에 256..511 이
// 되므로 실제로 쓰이는 자리는 1..255 뿐 — 배열이 257 이 아니라 256
// 이다.
type byteModel struct{ probs []uint16 }

func newByteModel() *byteModel {
	p := make([]uint16, 256)
	for i := range p {
		p[i] = probInit
	}
	return &byteModel{p}
}

func (m *byteModel) encode(e *rcEncoder, b byte) {
	ctx := 1
	for i := 7; i >= 0; i-- {
		bit := int(b>>uint(i)) & 1
		e.encodeBit(m.probs, ctx, bit)
		ctx = ctx<<1 | bit
	}
}

func (m *byteModel) decode(d *rcDecoder) byte {
	ctx := 1
	for i := 0; i < 8; i++ {
		ctx = ctx<<1 | d.decodeBit(m.probs, ctx)
	}
	return byte(ctx - 256)
}

func RangecoderEncode(src []byte) (out []byte, err error) {
	defer guard(&err)
	if len(src) == 0 {
		return putVarint(nil, 0), nil
	}
	e := newRcEncoder()
	m := newByteModel()
	for _, b := range src {
		m.encode(e, b)
	}
	e.flush()
	return append(putVarint(nil, uint64(len(src))), e.out...), nil
}

func RangecoderDecode(src []byte) (out []byte, err error) {
	defer guard(&err)
	n, pos := getLength(src, 0)
	if n == 0 {
		if pos != len(src) {
			fail("빈 입력인데 뒤에 바이트가 있다")
		}
		return []byte{}, nil
	}
	d := newRcDecoder(src, pos)
	m := newByteModel()
	result := make([]byte, 0, n)
	for i := 0; i < n; i++ {
		result = append(result, m.decode(d))
	}
	return result, nil
}
