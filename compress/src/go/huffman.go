package compresslib

// 캐노니컬 허프만 — SPEC §5.
//
// 트리를 만들지 않는다. 최적 길이 벡터는 하나가 아니어서(1,1,1,1 은 두
// 벌이 다 최적) 트리를 만들면 우선순위 큐의 동점 처리가 어느 쪽을
// 고를지 정하는데, 그 처리는 언어마다 다르다. package–merge 의 정렬 키
// (무게, 종류, 순번) 가 동점 처리 전부이고, 그 키 덕분에 결과가 빈도
// 벡터만의 함수가 된다.

import "sort"

const (
	huffMaxLength  = 15
	huffAlphabet   = 256
	huffTableBytes = huffAlphabet / 2
)

type coin struct {
	weight uint64
	// 0 = 기호 동전, 1 = 꾸러미. 무게가 같으면 기호 동전이 앞선다.
	kind int
	rank int
	syms []int
}

func coinLess(a, b coin) bool {
	if a.weight != b.weight {
		return a.weight < b.weight
	}
	if a.kind != b.kind {
		return a.kind < b.kind
	}
	return a.rank < b.rank
}

func codeLengths(freqs []uint64, limit int) []int {
	type used struct {
		freq uint64
		sym  int
	}
	var list []used
	for s, f := range freqs {
		if f > 0 {
			list = append(list, used{f, s})
		}
	}
	sort.Slice(list, func(i, j int) bool {
		if list[i].freq != list[j].freq {
			return list[i].freq < list[j].freq
		}
		return list[i].sym < list[j].sym
	})
	lengths := make([]int, len(freqs))
	m := len(list)
	if m == 0 {
		return lengths
	}
	if m == 1 {
		lengths[list[0].sym] = 1
		return lengths
	}
	if limit < 63 && m > 1<<uint(limit) {
		fail("기호 %d개는 길이 %d 로 못 담는다", m, limit)
	}
	coins := make([]coin, m)
	for j, u := range list {
		coins[j] = coin{u.freq, 0, j, []int{u.sym}}
	}
	level := append([]coin(nil), coins...)
	for round := 0; round < limit-1; round++ {
		packed := make([]coin, 0, len(level)/2)
		for i := 0; i+1 < len(level); i += 2 {
			syms := append(append([]int(nil), level[i].syms...),
				level[i+1].syms...)
			packed = append(packed, coin{
				level[i].weight + level[i+1].weight,
				1, len(packed), syms})
		}
		level = append(packed, coins...)
		sort.SliceStable(level, func(i, j int) bool {
			return coinLess(level[i], level[j])
		})
	}
	take := 2*m - 2
	if take > len(level) {
		take = len(level)
	}
	for i := 0; i < take; i++ {
		for _, s := range level[i].syms {
			lengths[s]++
		}
	}
	return lengths
}

func canonicalCodes(lengths []int) []int {
	blCount := make([]int, huffMaxLength+1)
	for _, l := range lengths {
		if l > 0 {
			if l > huffMaxLength {
				fail("부호 길이 %d 는 상한을 넘는다", l)
			}
			blCount[l]++
		}
	}
	nextCode := make([]int, huffMaxLength+2)
	code := 0
	for bits := 1; bits <= huffMaxLength; bits++ {
		code = (code + blCount[bits-1]) << 1
		nextCode[bits] = code
	}
	codes := make([]int, len(lengths))
	for s, l := range lengths {
		if l == 0 {
			continue
		}
		if nextCode[l] >= 1<<uint(l) {
			fail("부호표가 넘친다 — 길이 %d", l)
		}
		codes[s] = nextCode[l]
		nextCode[l]++
	}
	return codes
}

// 크래프트 합이 1 인지. 예외는 **기호 하나짜리 표** — 길이 1 하나라 늘
// 합이 1/2 이고, zeros_64k 처럼 한 바이트만 있는 파일에서 반드시
// 나온다.
func checkComplete(lengths []int) {
	checkCompleteMax(lengths, huffMaxLength)
}

func checkCompleteMax(lengths []int, maxLength int) {
	var total uint64
	used, only := 0, 0
	for _, l := range lengths {
		if l > 0 {
			total += uint64(1) << uint(maxLength-l)
			used++
			only = l
		}
	}
	full := uint64(1) << uint(maxLength)
	if total > full {
		fail("부호표가 넘친다 (크래프트 합 > 1)")
	}
	if total < full && !(used == 1 && only == 1) {
		fail("부호표가 모자란다 (크래프트 합 < 1)")
	}
}

type bitReader interface{ readBit() int }

// 캐노니컬 복호기 — 트리를 안 만든다. 길이별 첫 부호와 첫 자리만 있으면
// 비트를 하나씩 받아 가며 판정할 수 있다.
type huffDecoder struct {
	symbols    []int
	count      []int
	firstCode  []int
	firstIndex []int
	maxLength  int
}

func newHuffDecoder(lengths []int) *huffDecoder {
	return newHuffDecoderMax(lengths, huffMaxLength)
}

// bzip2 는 부호 길이가 20까지 간다 (SPEC §15.4). 기본값은 15 그대로다.
func newHuffDecoderMax(lengths []int, maxLength int) *huffDecoder {
	type pair struct{ length, sym int }
	var pairs []pair
	for s, l := range lengths {
		if l > 0 {
			pairs = append(pairs, pair{l, s})
		}
	}
	sort.Slice(pairs, func(i, j int) bool {
		if pairs[i].length != pairs[j].length {
			return pairs[i].length < pairs[j].length
		}
		return pairs[i].sym < pairs[j].sym
	})
	d := &huffDecoder{
		count:      make([]int, maxLength+1),
		firstCode:  make([]int, maxLength+2),
		firstIndex: make([]int, maxLength+2),
		maxLength:  maxLength,
	}
	for _, p := range pairs {
		d.symbols = append(d.symbols, p.sym)
		d.count[p.length]++
	}
	code, index := 0, 0
	for l := 1; l <= maxLength; l++ {
		code = (code + d.count[l-1]) << 1
		d.firstCode[l] = code
		d.firstIndex[l] = index
		index += d.count[l]
	}
	return d
}

func (d *huffDecoder) read(r bitReader) int {
	code := 0
	for l := 1; l <= d.maxLength; l++ {
		code = code<<1 | r.readBit()
		off := code - d.firstCode[l]
		if d.count[l] > 0 && off < d.count[l] {
			return d.symbols[d.firstIndex[l]+off]
		}
	}
	fail("부호표에 없는 비트열")
	return 0
}

func huffNibble(table []byte, sym int) int {
	b := table[sym>>1]
	if sym&1 == 1 {
		return int(b & 0x0F)
	}
	return int(b >> 4)
}

func huffPackTable(lengths []int) []byte {
	table := make([]byte, huffTableBytes)
	for s := 0; s < huffAlphabet; s++ {
		v := byte(lengths[s] & 0x0F)
		if s&1 == 1 {
			table[s>>1] |= v
		} else {
			table[s>>1] |= v << 4
		}
	}
	return table
}

func HuffmanEncode(src []byte) (out []byte, err error) {
	defer guard(&err)
	if len(src) == 0 {
		return putVarint(nil, 0), nil
	}
	freqs := make([]uint64, huffAlphabet)
	for _, b := range src {
		freqs[b]++
	}
	lengths := codeLengths(freqs, huffMaxLength)
	codes := canonicalCodes(lengths)
	var w msbWriter
	for _, b := range src {
		w.writeBits(uint64(codes[b]), lengths[b])
	}
	w.flush()
	result := putVarint(nil, uint64(len(src)))
	result = append(result, huffPackTable(lengths)...)
	return append(result, w.out...), nil
}

func HuffmanDecode(src []byte) (out []byte, err error) {
	defer guard(&err)
	n, pos := getLength(src, 0)
	if n == 0 {
		if pos != len(src) {
			fail("빈 입력인데 뒤에 바이트가 있다")
		}
		return []byte{}, nil
	}
	if len(src) < pos+huffTableBytes {
		fail("부호 길이 표가 잘렸다")
	}
	table := src[pos : pos+huffTableBytes]
	lengths := make([]int, huffAlphabet)
	for s := 0; s < huffAlphabet; s++ {
		lengths[s] = huffNibble(table, s)
	}
	checkComplete(lengths)
	dec := newHuffDecoder(lengths)
	r := &msbReader{src: src, pos: pos + huffTableBytes}
	result := make([]byte, 0, n)
	for i := 0; i < n; i++ {
		result = append(result, byte(dec.read(r)))
	}
	return result, nil
}
