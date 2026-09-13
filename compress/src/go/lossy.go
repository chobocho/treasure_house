package compresslib

// 손실 압축 — SPEC §19.
//
// 여기까지는 한 비트도 안 버렸다. 이 모듈은 **일부러 버린다.** 버리는
// 자리는 딱 하나, 양자화다 — DCT 도 PNG 필터도 그 자체로는 안 버린다.
//
// **레지스트리에 오르는 코덱은 PNG 쪽** 이다. 왕복하는 것이 그것뿐이다.
// 손실 코덱에 골든 벡터를 붙이면 부호기만 못 박는 꼴이다.

const (
	dctScale   = 13
	dctRound   = 1 << (dctScale - 1)
	lossyBlock = 8
	pngWidth   = 256 // 골든 코덱이 쓰는 행 폭 (§19.5)
	pngBpp     = 1
	jpegEob    = 255
)

// DCT-TABLE-BEGIN — gen_tables.py 가 다섯 언어를 대조한다 (§19.2)
var dctTable = [64]int{
	2896, 2896, 2896, 2896, 2896, 2896, 2896, 2896,
	4017, 3406, 2276, 799, -799, -2276, -3406, -4017,
	3784, 1567, -1567, -3784, -3784, -1567, 1567, 3784,
	3406, -799, -4017, -2276, 2276, 4017, 799, -3406,
	2896, -2896, -2896, 2896, 2896, -2896, -2896, 2896,
	2276, -4017, 799, 3406, -3406, -799, 4017, -2276,
	1567, -3784, 3784, -1567, -1567, 3784, -3784, 1567,
	799, -2276, 3406, -4017, 4017, -3406, 2276, -799}

// DCT-TABLE-END

// JPEGQ-TABLE-BEGIN — gen_tables.py 가 다섯 언어를 대조한다 (§19.4)
var jpegQuant = [64]int{
	16, 11, 10, 16, 24, 40, 51, 61,
	12, 12, 14, 19, 26, 58, 60, 55,
	14, 13, 16, 24, 40, 57, 69, 56,
	14, 17, 22, 29, 51, 87, 80, 62,
	18, 22, 37, 56, 68, 109, 103, 77,
	24, 35, 55, 64, 81, 104, 113, 92,
	49, 64, 78, 87, 103, 121, 120, 101,
	72, 92, 95, 98, 112, 100, 103, 99}

// JPEGQ-TABLE-END

// ADPCMSTEP-TABLE-BEGIN — gen_tables.py 가 대조한다 (§19.6)
var adpcmStep = [89]int{
	7, 8, 9, 10, 11, 12, 13, 14, 16, 17, 19, 21, 23, 25, 28, 31,
	34, 37, 41, 45, 50, 55, 60, 66, 73, 80, 88, 97, 107, 118, 130,
	143, 157, 173, 190, 209, 230, 253, 279, 307, 337, 371, 408, 449,
	494, 544, 598, 658, 724, 796, 876, 963, 1060, 1166, 1282, 1411,
	1552, 1707, 1878, 2066, 2272, 2499, 2749, 3024, 3327, 3660, 4026,
	4428, 4871, 5358, 5894, 6484, 7132, 7845, 8630, 9493, 10442, 11487,
	12635, 13899, 15289, 16818, 18500, 20350, 22385, 24623, 27086,
	29794, 32767}

// ADPCMSTEP-TABLE-END

// ADPCMINDEX-TABLE-BEGIN — gen_tables.py 가 대조한다 (§19.6)
var adpcmIndex = [16]int{-1, -1, -1, -1, 2, 4, 6, 8,
	-1, -1, -1, -1, 2, 4, 6, 8}

// ADPCMINDEX-TABLE-END

// 8×8 을 대각선으로 훑는 순서. 표가 아니라 규칙이라 여기서 만든다.
// intcode 의 zigzag 와 이름이 겹치지 않게 zigzagOrder 로 둔다.
var zigzagOrder = func() [64]int {
	var out [64]int
	k := 0
	for s := 0; s < 15; s++ {
		var cells [][2]int
		for x := 0; x < 8; x++ {
			y := s - x
			if y >= 0 && y < 8 {
				cells = append(cells, [2]int{x, y})
			}
		}
		if s%2 == 1 {
			for i, j := 0, len(cells)-1; i < j; i, j = i+1, j-1 {
				cells[i], cells[j] = cells[j], cells[i]
			}
		}
		for _, c := range cells {
			out[k] = c[1]*8 + c[0]
			k++
		}
	}
	return out
}()

// 버리는 곳은 여기 하나뿐이다 (§19.3).
func quantise(v, q int, deadZone bool) int {
	if deadZone {
		if v < 0 {
			return -((-v) / q)
		}
		return v / q
	}
	if v < 0 {
		return -((-v*2 + q) / (2 * q))
	}
	return (v*2 + q) / (2 * q)
}

func dequantise(v, q int) int { return v * q }

// 8×8 정수 DCT. 1차원 변환 두 번, 각각 반올림 (§19.2).
func fdct8(block [64]int) [64]int {
	var tmp, out [64]int
	for u := 0; u < 8; u++ {
		for y := 0; y < 8; y++ {
			s := 0
			for x := 0; x < 8; x++ {
				s += dctTable[u*8+x] * block[x*8+y]
			}
			tmp[u*8+y] = (s + dctRound) >> dctScale
		}
	}
	for u := 0; u < 8; u++ {
		for v := 0; v < 8; v++ {
			s := 0
			for y := 0; y < 8; y++ {
				s += dctTable[v*8+y] * tmp[u*8+y]
			}
			out[u*8+v] = (s + dctRound) >> dctScale
		}
	}
	return out
}

func idct8(coef [64]int) [64]int {
	var tmp, out [64]int
	for x := 0; x < 8; x++ {
		for v := 0; v < 8; v++ {
			s := 0
			for u := 0; u < 8; u++ {
				s += dctTable[u*8+x] * coef[u*8+v]
			}
			tmp[x*8+v] = (s + dctRound) >> dctScale
		}
	}
	for x := 0; x < 8; x++ {
		for y := 0; y < 8; y++ {
			s := 0
			for v := 0; v < 8; v++ {
				s += dctTable[v*8+y] * tmp[x*8+v]
			}
			out[x*8+y] = (s + dctRound) >> dctScale
		}
	}
	return out
}

// 품질 1~100 로 JPEG 표준표를 늘리고 줄인다 (§19.4).
func quantTable(quality int) [64]int {
	if quality < 1 || quality > 100 {
		fail("품질은 1~100 이다: %d", quality)
	}
	scale := 200 - 2*quality
	if quality < 50 {
		scale = 5000 / quality
	}
	var out [64]int
	for i, base := range jpegQuant {
		q := (base*scale + 50) / 100
		if q < 1 {
			q = 1
		}
		if q > 255 {
			q = 255
		}
		out[i] = q
	}
	return out
}

// jpeglite — 우리 형식이다. JPEG 이 아니다 (§19.4).
var jpegMagic = []byte{'J', 'L', '1'}

func JpegliteEncode(pixels []byte, width, height, quality int) []byte {
	if width*height != len(pixels) {
		fail("픽셀 수가 너비×높이와 다르다")
	}
	if width <= 0 || height <= 0 || width > 0xFFFF || height > 0xFFFF {
		fail("크기가 범위를 벗어났다")
	}
	qt := quantTable(quality)
	var stream []byte
	for by := 0; by < height; by += lossyBlock {
		for bx := 0; bx < width; bx += lossyBlock {
			var block [64]int
			for y := 0; y < lossyBlock; y++ {
				sy := min(by+y, height-1)
				for x := 0; x < lossyBlock; x++ {
					sx := min(bx+x, width-1)
					block[x*8+y] = int(pixels[sy*width+sx]) - 128
				}
			}
			coef := fdct8(block)
			run := 0
			for k := 0; k < 64; k++ {
				idx := zigzagOrder[k]
				v := quantise(coef[idx], qt[idx], k > 0)
				if v == 0 && k > 0 {
					run++
					continue
				}
				for run >= jpegEob {
					stream = append(stream, byte(jpegEob-1), 0)
					run -= jpegEob
				}
				stream = append(stream, byte(run))
				var z uint64
				if v >= 0 {
					z = uint64(v) << 1
				} else {
					z = uint64(-v)<<1 - 1
				}
				stream = putVarint(stream, z)
				run = 0
			}
			stream = append(stream, byte(jpegEob))
		}
	}
	out := append([]byte(nil), jpegMagic...)
	out = append(out, byte(width), byte(width>>8),
		byte(height), byte(height>>8), byte(quality))
	body, err := HuffmanEncode(stream)
	if err != nil {
		fail("%v", err)
	}
	return append(out, body...)
}

// (픽셀, 너비, 높이). 원본과 같지 않다 — 그게 이 형식의 약속이다.
func JpegliteDecode(src []byte) ([]byte, int, int) {
	if len(src) < 8 || src[0] != 'J' || src[1] != 'L' || src[2] != '1' {
		fail("jpeglite 매직이 아니다")
	}
	width := int(src[3]) | int(src[4])<<8
	height := int(src[5]) | int(src[6])<<8
	qt := quantTable(int(src[7]))
	stream, err := HuffmanDecode(src[8:])
	if err != nil {
		fail("%v", err)
	}
	pos := 0
	pixels := make([]byte, width*height)
	for by := 0; by < height; by += lossyBlock {
		for bx := 0; bx < width; bx += lossyBlock {
			var coef [64]int
			k := 0
			// 끝 표시는 반드시 읽어 치운다 — 64개가 다 실린 블록에서
			// 안 먹고 나가면 다음 블록이 그 255 를 자기 EOB 로 읽는다.
			for {
				if pos >= len(stream) {
					fail("계수 스트림이 잘렸다")
				}
				run := int(stream[pos])
				pos++
				if run == jpegEob {
					break
				}
				k += run
				if k >= 64 {
					fail("0 런이 블록을 넘는다")
				}
				var z uint64
				z, pos = getVarint(stream, pos)
				v := int(z >> 1)
				if z&1 != 0 {
					v = -int((z + 1) >> 1)
				}
				coef[zigzagOrder[k]] = dequantise(v, qt[zigzagOrder[k]])
				k++
			}
			block := idct8(coef)
			for y := 0; y < lossyBlock; y++ {
				sy := by + y
				if sy >= height {
					break
				}
				for x := 0; x < lossyBlock; x++ {
					sx := bx + x
					if sx >= width {
						break
					}
					pixels[sy*width+sx] = byte(clampInt(
						block[x*8+y]+128, 0, 255))
				}
			}
		}
	}
	return pixels, width, height
}

// 왼쪽·위·왼쪽위 가운데 a+b-c 에 가장 가까운 것. 동점은 a, 그다음 b.
func paeth(a, b, c int) int {
	p := a + b - c
	pa, pb, pc := abs(p-a), abs(p-b), abs(p-c)
	if pa <= pb && pa <= pc {
		return a
	}
	if pb <= pc {
		return b
	}
	return c
}

func abs(v int) int {
	if v < 0 {
		return -v
	}
	return v
}

func filterRow(row, prev []byte, kind, bpp int) []byte {
	out := make([]byte, len(row))
	for i := range row {
		v := int(row[i])
		left, up, upleft := 0, 0, 0
		if i >= bpp {
			left = int(row[i-bpp])
		}
		if i < len(prev) {
			up = int(prev[i])
		}
		if i >= bpp && i-bpp < len(prev) {
			upleft = int(prev[i-bpp])
		}
		var d int
		switch kind {
		case 0:
			d = v
		case 1:
			d = v - left
		case 2:
			d = v - up
		case 3:
			d = v - (left+up)>>1
		default:
			d = v - paeth(left, up, upleft)
		}
		out[i] = byte(d)
	}
	return out
}

func unfilterRow(row, prev []byte, kind, bpp int) []byte {
	out := make([]byte, len(row))
	for i := range row {
		d := int(row[i])
		left, up, upleft := 0, 0, 0
		if i >= bpp {
			left = int(out[i-bpp])
		}
		if i < len(prev) {
			up = int(prev[i])
		}
		if i >= bpp && i-bpp < len(prev) {
			upleft = int(prev[i-bpp])
		}
		var v int
		switch kind {
		case 0:
			v = d
		case 1:
			v = d + left
		case 2:
			v = d + up
		case 3:
			v = d + (left+up)>>1
		case 4:
			v = d + paeth(left, up, upleft)
		default:
			fail("없는 필터 종류: %d", kind)
		}
		out[i] = byte(v)
	}
	return out
}

// 줄마다 다섯 후보 가운데 절댓값 합이 가장 작은 것을 고른다 (§19.5).
func pngFilter(data []byte, width, bpp int) []byte {
	var out []byte
	var prev []byte
	for off := 0; off < len(data); off += width {
		end := off + width
		if end > len(data) {
			end = len(data)
		}
		row := data[off:end]
		bestKind := 0
		var bestRow []byte
		bestScore := -1
		for kind := 0; kind < 5; kind++ {
			cand := filterRow(row, prev, kind, bpp)
			score := 0
			for _, b := range cand {
				if b < 128 {
					score += int(b)
				} else {
					score += 256 - int(b)
				}
			}
			if bestScore < 0 || score < bestScore {
				bestKind, bestRow, bestScore = kind, cand, score
			}
		}
		out = append(out, byte(bestKind))
		out = append(out, bestRow...)
		prev = row
	}
	return out
}

func pngUnfilter(data []byte, width, bpp int) []byte {
	var out []byte
	var prev []byte
	pos := 0
	for pos < len(data) {
		kind := int(data[pos])
		pos++
		n := width
		if pos+n > len(data) {
			n = len(data) - pos
		}
		row := unfilterRow(data[pos:pos+n], prev, kind, bpp)
		pos += n
		out = append(out, row...)
		prev = row
	}
	return out
}

// 골든 코덱 — 이 모듈에서 유일하게 왕복한다 (§19.1).
func LossyEncode(src []byte) (out []byte, err error) {
	defer guard(&err)
	if len(src) == 0 {
		return putVarint(nil, 0), nil
	}
	body := deflateRaw(pngFilter(src, pngWidth, pngBpp))
	return append(putVarint(nil, uint64(len(src))), body...), nil
}

func LossyDecode(src []byte) (out []byte, err error) {
	defer guard(&err)
	n, pos := getLength(src, 0)
	if n == 0 {
		if pos != len(src) {
			fail("빈 입력인데 뒤에 바이트가 있다")
		}
		return []byte{}, nil
	}
	result := pngUnfilter(inflateRaw(src[pos:]), pngWidth, pngBpp)
	if len(result) != n {
		fail("푼 길이가 헤더와 다르다: %d != %d", len(result), n)
	}
	return result, nil
}

// IMA ADPCM — 예측기를 안 보내는 것이 요점이다 (§19.6).
func AdpcmEncode(samples []int) []byte {
	var out []byte
	predictor, index, half := 0, 0, -1
	for _, s := range samples {
		step := adpcmStep[index]
		diff := s - predictor
		code := 0
		if diff < 0 {
			code = 8
			diff = -diff
		}
		mag := diff * 4 / step
		if mag > 7 {
			mag = 7
		}
		code |= mag
		delta := step >> 3
		if mag&4 != 0 {
			delta += step
		}
		if mag&2 != 0 {
			delta += step >> 1
		}
		if mag&1 != 0 {
			delta += step >> 2
		}
		if code&8 != 0 {
			predictor -= delta
		} else {
			predictor += delta
		}
		predictor = clampInt(predictor, -32768, 32767)
		index = clampInt(index+adpcmIndex[code&7], 0, 88)
		if half < 0 {
			half = code
		} else {
			out = append(out, byte(half<<4|code))
			half = -1
		}
	}
	if half >= 0 {
		out = append(out, byte(half<<4))
	}
	return out
}

func AdpcmDecode(data []byte, count int) []int {
	out := make([]int, 0, count)
	predictor, index := 0, 0
	for i := 0; i < count; i++ {
		if i>>1 >= len(data) {
			fail("ADPCM 스트림이 잘렸다")
		}
		b := int(data[i>>1])
		code := b & 0x0F
		if i&1 == 0 {
			code = b >> 4
		}
		step := adpcmStep[index]
		mag := code & 7
		delta := step >> 3
		if mag&4 != 0 {
			delta += step
		}
		if mag&2 != 0 {
			delta += step >> 1
		}
		if mag&1 != 0 {
			delta += step >> 2
		}
		if code&8 != 0 {
			predictor -= delta
		} else {
			predictor += delta
		}
		predictor = clampInt(predictor, -32768, 32767)
		index = clampInt(index+adpcmIndex[code&7], 0, 88)
		out = append(out, predictor)
	}
	return out
}

func clampInt(v, lo, hi int) int {
	if v < lo {
		return lo
	}
	if v > hi {
		return hi
	}
	return v
}
