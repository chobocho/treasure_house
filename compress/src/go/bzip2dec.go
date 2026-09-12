package compresslib

// bzip2 복호기 — SPEC §15.
//
// bzip2 가 쓰는 조각은 이미 다 있다. BWT·MTF·0런·캐노니컬 허프만.
// bzip2 가 더한 것은 **조립** 이라, 부호기는 안 만든다 — 진짜 bzip2 가
// 만든 파일을 푸는 편이 훨씬 센 주장이다.
//
// 가장 잘 속는 자리는 CRC 다. bzip2 의 CRC-32 는 gzip 것과 다항식은
// 같아도 **반사가 없다.** gzip 표를 그대로 쓰면 빈 입력만 맞는다
// (§15.6).

const (
	bzBlockMagic = 0x314159265359
	bzEndMagic   = 0x177245385090
	bzMaxGroups  = 6
	bzGroupSize  = 50
	bzMaxCodeLen = 20
	bzRunA       = 0
	bzRunB       = 1
)

// 반사 없는 CRC-32/BZIP2 표. 다항식 0x04C11DB7 을 위에서부터 민다.
var bzCrcTable = func() [256]uint32 {
	var t [256]uint32
	for i := 0; i < 256; i++ {
		c := uint32(i) << 24
		for k := 0; k < 8; k++ {
			if c&0x80000000 != 0 {
				c = c<<1 ^ 0x04C11DB7
			} else {
				c <<= 1
			}
		}
		t[i] = c
	}
	return t
}()

func crc32Bzip2(data []byte) uint32 {
	c := uint32(0xFFFFFFFF)
	for _, b := range data {
		c = bzCrcTable[(c>>24^uint32(b))&0xFF] ^ c<<8
	}
	return c ^ 0xFFFFFFFF
}

// MSB 먼저. bzip2 는 48비트 매직을 읽어야 해서 넓은 읽기가 필요하다.
type bzReader struct {
	src []byte
	pos int
	buf byte
	n   int
}

func (r *bzReader) readBit() int {
	if r.n == 0 {
		if r.pos >= len(r.src) {
			fail("bzip2 스트림이 바닥났다")
		}
		r.buf = r.src[r.pos]
		r.pos++
		r.n = 8
	}
	r.n--
	return int(r.buf>>uint(r.n)) & 1
}

func (r *bzReader) readBits(count int) uint64 {
	var v uint64
	for i := 0; i < count; i++ {
		v = v<<1 | uint64(r.readBit())
	}
	return v
}

// 같은 바이트 넷 뒤의 한 바이트는 "더 붙일 개수" 다 (§15.5).
func bzRle1Decode(src []byte) []byte {
	var out []byte
	i, n := 0, len(src)
	for i < n {
		b := src[i]
		run := 1
		for run < 4 && i+run < n && src[i+run] == b {
			run++
		}
		for k := 0; k < run; k++ {
			out = append(out, b)
		}
		i += run
		if run == 4 {
			if i >= n {
				fail("RLE1 의 개수 바이트가 없다")
			}
			for k := 0; k < int(src[i]); k++ {
				out = append(out, b)
			}
			i++
		}
	}
	return out
}

func bzReadSymbolMap(r *bzReader) []int {
	var used []int
	groups := r.readBits(16)
	for g := 0; g < 16; g++ {
		if groups&(uint64(1)<<uint(15-g)) != 0 {
			bits := r.readBits(16)
			for k := 0; k < 16; k++ {
				if bits&(uint64(1)<<uint(15-k)) != 0 {
					used = append(used, g*16+k)
				}
			}
		}
	}
	if len(used) == 0 {
		fail("기호 지도가 비었다")
	}
	return used
}

// 단항으로 적힌 MTF 선택자. 값이 곧 "몇 번째 표" 다.
func bzReadSelectors(r *bzReader, nGroups, nSelectors int) []int {
	mtf := make([]int, nGroups)
	for i := range mtf {
		mtf[i] = i
	}
	out := make([]int, 0, nSelectors)
	for i := 0; i < nSelectors; i++ {
		j := 0
		for r.readBit() != 0 {
			j++
			if j >= nGroups {
				fail("선택자가 표 개수를 넘는다")
			}
		}
		v := mtf[j]
		copy(mtf[1:j+1], mtf[0:j])
		mtf[0] = v
		out = append(out, v)
	}
	return out
}

func bzReadTables(r *bzReader, nGroups, alphaSize int) []*huffDecoder {
	tables := make([]*huffDecoder, 0, nGroups)
	for g := 0; g < nGroups; g++ {
		length := int(r.readBits(5))
		lengths := make([]int, 0, alphaSize)
		for s := 0; s < alphaSize; s++ {
			for {
				if length < 1 || length > bzMaxCodeLen {
					fail("부호 길이가 범위를 벗어났다: %d", length)
				}
				if r.readBit() == 0 {
					break
				}
				if r.readBit() != 0 {
					length--
				} else {
					length++
				}
			}
			lengths = append(lengths, length)
		}
		checkCompleteMax(lengths, bzMaxCodeLen)
		dec := newHuffDecoderMax(lengths, bzMaxCodeLen)
		tables = append(tables, dec)
	}
	return tables
}

// 허프만 → MTF 지표 열. RUNA/RUNB 는 여기서 0 의 런으로 편다.
func bzReadBlockSymbols(r *bzReader, tables []*huffDecoder,
	selectors []int, alphaSize, limit int) []int {
	eob := alphaSize - 1
	var out []int
	group, left := 0, 0
	var dec *huffDecoder
	var run, weight uint64 = 0, 1
	for {
		if left == 0 {
			if group >= len(selectors) {
				fail("선택자가 모자란다")
			}
			dec = tables[selectors[group]]
			group++
			left = bzGroupSize
		}
		left--
		sym := dec.read(r)
		if sym <= bzRunB {
			run += uint64(sym+1) * weight
			weight <<= 1
			if run > uint64(limit) {
				fail("0 런이 블록 크기를 넘는다")
			}
			continue
		}
		if run > 0 {
			for k := uint64(0); k < run; k++ {
				out = append(out, 0)
			}
			run, weight = 0, 1
		}
		if sym == eob {
			return out
		}
		out = append(out, sym-1)
		if len(out) > limit {
			fail("블록이 상한을 넘는다")
		}
	}
}

// 쓰인 값들만 놓고 MTF 를 되돌린다 — 기호 지도가 여기서 값을 한다.
func bzInverseMtf(indices, used []int) []byte {
	table := append([]int(nil), used...)
	out := make([]byte, 0, len(indices))
	for _, i := range indices {
		if i >= len(table) {
			fail("MTF 지표가 알파벳을 넘는다")
		}
		v := table[i]
		out = append(out, byte(v))
		if i != 0 {
			copy(table[1:i+1], table[0:i])
			table[0] = v
		}
	}
	return out
}

func Bzip2decDecode(src []byte) (out []byte, err error) {
	defer guard(&err)
	if len(src) < 4 || src[0] != 'B' || src[1] != 'Z' || src[2] != 'h' {
		fail("bzip2 매직이 아니다")
	}
	level := int(src[3]) - 0x30
	if level < 1 || level > 9 {
		fail("블록 크기 등급이 1~9 가 아니다: %d", level)
	}
	limit := level * 100000
	r := &bzReader{src: src, pos: 4}
	var result []byte
	var combined uint32
	for {
		magic := r.readBits(48)
		if magic == bzEndMagic {
			want := uint32(r.readBits(32))
			if want != combined {
				fail("합친 CRC 가 다르다")
			}
			return result, nil
		}
		if magic != bzBlockMagic {
			fail("블록 매직이 아니다")
		}
		blockCrc := uint32(r.readBits(32))
		if r.readBit() != 0 {
			fail("무작위화된 블록은 지원하지 않는다")
		}
		origPtr := uint32(r.readBits(24))
		used := bzReadSymbolMap(r)
		alphaSize := len(used) + 2
		nGroups := int(r.readBits(3))
		if nGroups < 2 || nGroups > bzMaxGroups {
			fail("표 개수가 2~6 이 아니다: %d", nGroups)
		}
		nSelectors := int(r.readBits(15))
		selectors := bzReadSelectors(r, nGroups, nSelectors)
		tables := bzReadTables(r, nGroups, alphaSize)
		indices := bzReadBlockSymbols(r, tables, selectors,
			alphaSize, limit)
		lColumn := bzInverseMtf(indices, used)
		if int(origPtr) >= len(lColumn) {
			fail("origPtr 가 블록 밖이다")
		}
		block := bzRle1Decode(bwtInverseBlock(lColumn, origPtr))
		if crc32Bzip2(block) != blockCrc {
			fail("블록 CRC 가 다르다")
		}
		combined = (combined<<1 | combined>>31) ^ blockCrc
		result = append(result, block...)
	}
}
