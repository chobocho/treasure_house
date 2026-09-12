package compresslib

// LZMA1 복호기 — SPEC §16.
//
// §8 의 레인지 코더를 LZMA 것으로 쓴 이유가 이 파일이다. 같은 코더에
// LZMA 의 문맥 모델만 얹으면 진짜 xz 가 만든 파일이 풀린다.
//
// 읽는 것은 LZMA1 "alone" 형식이다. .xz 컨테이너는 다른 틀이고 12부에서
// 말로만 다룬다 — "LZMA 를 푼다" 와 ".xz 를 푼다" 는 다른 주장이다.

const (
	lzmaNumStates         = 12
	lzmaNumPosBitsMax     = 4
	lzmaNumLenToPosStates = 4
	lzmaNumAlignBits      = 4
	lzmaEndPosModelIndex  = 14
	lzmaNumFullDistances  = 1 << (lzmaEndPosModelIndex >> 1)
	lzmaMatchMinLen       = 2
	lzmaUnknownSize       = uint64(0xFFFFFFFFFFFFFFFF)
	lzmaEndMarker         = uint32(0xFFFFFFFF)
	lzmaMaxOutput         = 1 << 32
)

func lzmaProbs(n int) []uint16 {
	p := make([]uint16, n)
	for i := range p {
		p[i] = probInit
	}
	return p
}

// 위에서부터 내려가는 이진 트리. 결과는 numBits 짜리 값.
func lzmaBitTree(dec *rcDecoder, probs []uint16,
	offset, numBits int) int {
	m := 1
	for i := 0; i < numBits; i++ {
		m = m<<1 + dec.decodeBit(probs, offset+m)
	}
	return m - 1<<uint(numBits)
}

// 같은 트리인데 비트를 **거꾸로** 모은다 — 거리의 아래 비트가 이렇다.
func lzmaBitTreeReverse(dec *rcDecoder, probs []uint16,
	offset, numBits int) uint32 {
	m := 1
	var sym uint32
	for i := 0; i < numBits; i++ {
		bit := dec.decodeBit(probs, offset+m)
		m = m<<1 + bit
		sym |= uint32(bit) << uint(i)
	}
	return sym
}

// 길이 복호기. 2..273 을 세 구간(8+8+256)으로 나눠 적는다.
type lzmaLengthCoder struct {
	choice []uint16
	low    []uint16
	mid    []uint16
	high   []uint16
}

func newLzmaLengthCoder(posStates int) *lzmaLengthCoder {
	return &lzmaLengthCoder{
		choice: lzmaProbs(2),
		low:    lzmaProbs(posStates * 8),
		mid:    lzmaProbs(posStates * 8),
		high:   lzmaProbs(256),
	}
}

func (c *lzmaLengthCoder) decode(dec *rcDecoder, posState int) int {
	if dec.decodeBit(c.choice, 0) == 0 {
		return lzmaBitTree(dec, c.low, posState*8, 3)
	}
	if dec.decodeBit(c.choice, 1) == 0 {
		return 8 + lzmaBitTree(dec, c.mid, posState*8, 3)
	}
	return 16 + lzmaBitTree(dec, c.high, 0, 8)
}

type lzmaHeader struct {
	lc, lp, pb int
	dictSize   uint32
	size       uint64
	pos        int
}

func lzmaParseHeader(src []byte) lzmaHeader {
	if len(src) < 13 {
		fail("LZMA 머리가 너무 짧다")
	}
	prop := int(src[0])
	if prop >= 9*5*5 {
		fail("속성 바이트가 범위를 넘는다: %d", prop)
	}
	var h lzmaHeader
	h.lc = prop % 9
	rest := prop / 9
	h.lp = rest % 5
	h.pb = rest / 5
	for i := 0; i < 4; i++ {
		h.dictSize |= uint32(src[1+i]) << uint(8*i)
	}
	for i := 0; i < 8; i++ {
		h.size |= uint64(src[5+i]) << uint(8*i)
	}
	if h.size != lzmaUnknownSize && h.size > lzmaMaxOutput {
		fail("원본 길이가 너무 크다")
	}
	h.pos = 13
	return h
}

func LzmadecDecode(src []byte) (out []byte, err error) {
	defer guard(&err)
	h := lzmaParseHeader(src)
	dec := newRcDecoder(src, h.pos)
	posStates := 1 << uint(h.pb)
	posMask := posStates - 1
	lpMask := 1<<uint(h.lp) - 1

	isMatch := lzmaProbs(lzmaNumStates << lzmaNumPosBitsMax)
	isRep := lzmaProbs(lzmaNumStates)
	isRepG0 := lzmaProbs(lzmaNumStates)
	isRepG1 := lzmaProbs(lzmaNumStates)
	isRepG2 := lzmaProbs(lzmaNumStates)
	isRep0Long := lzmaProbs(lzmaNumStates << lzmaNumPosBitsMax)
	posSlot := lzmaProbs(lzmaNumLenToPosStates * 64)
	specPos := lzmaProbs(lzmaNumFullDistances -
		lzmaEndPosModelIndex + 1)
	alignProbs := lzmaProbs(1 << lzmaNumAlignBits)
	literal := lzmaProbs(0x300 << uint(h.lc+h.lp))
	lenCoder := newLzmaLengthCoder(posStates)
	repLenCoder := newLzmaLengthCoder(posStates)

	var result []byte
	state := 0
	var rep0, rep1, rep2, rep3 uint32

	for h.size == lzmaUnknownSize || uint64(len(result)) < h.size {
		posState := len(result) & posMask
		midx := state<<lzmaNumPosBitsMax + posState
		var length int
		if dec.decodeBit(isMatch, midx) == 0 {
			prev := 0
			if len(result) > 0 {
				prev = int(result[len(result)-1])
			}
			litState := (len(result)&lpMask)<<uint(h.lc) +
				prev>>uint(8-h.lc)
			base := 0x300 * litState
			symbol := 1
			if state >= 7 {
				// 일치 뒤의 리터럴 — 앞 일치의 같은 자리에 견준다
				if int(rep0)+1 > len(result) {
					fail("거리가 지금까지 낸 것보다 멀다")
				}
				matchByte := int(result[len(result)-int(rep0)-1])
				for symbol < 0x100 {
					matchBit := (matchByte >> 7) & 1
					matchByte = (matchByte << 1) & 0xFF
					bit := dec.decodeBit(literal,
						base+(1+matchBit)<<8+symbol)
					symbol = symbol<<1 | bit
					if matchBit != bit {
						break
					}
				}
			}
			for symbol < 0x100 {
				symbol = symbol<<1 | dec.decodeBit(literal, base+symbol)
			}
			result = append(result, byte(symbol))
			switch {
			case state < 4:
				state = 0
			case state < 10:
				state -= 3
			default:
				state -= 6
			}
			continue
		}

		if dec.decodeBit(isRep, state) != 0 {
			// 지난 거리 넷 가운데 하나를 다시 쓴다 (§16.4)
			if len(result) == 0 {
				fail("첫 기호가 되풀이 일치다")
			}
			if dec.decodeBit(isRepG0, state) == 0 {
				if dec.decodeBit(isRep0Long, midx) == 0 {
					if state < 7 {
						state = 9
					} else {
						state = 11
					}
					if int(rep0)+1 > len(result) {
						fail("거리가 지금까지 낸 것보다 멀다")
					}
					result = append(result,
						result[len(result)-int(rep0)-1])
					continue
				}
			} else {
				var dist uint32
				if dec.decodeBit(isRepG1, state) == 0 {
					dist = rep1
				} else {
					if dec.decodeBit(isRepG2, state) == 0 {
						dist = rep2
					} else {
						dist = rep3
						rep3 = rep2
					}
					rep2 = rep1
				}
				rep1 = rep0
				rep0 = dist
			}
			length = repLenCoder.decode(dec, posState) + lzmaMatchMinLen
			if state < 7 {
				state = 8
			} else {
				state = 11
			}
		} else {
			rep3, rep2, rep1 = rep2, rep1, rep0
			length = lenCoder.decode(dec, posState) + lzmaMatchMinLen
			if state < 7 {
				state = 7
			} else {
				state = 10
			}
			slotState := length - lzmaMatchMinLen
			if slotState > lzmaNumLenToPosStates-1 {
				slotState = lzmaNumLenToPosStates - 1
			}
			slot := lzmaBitTree(dec, posSlot, slotState*64, 6)
			if slot < 4 {
				rep0 = uint32(slot)
			} else {
				direct := slot>>1 - 1
				rep0 = uint32(2|slot&1) << uint(direct)
				if slot < lzmaEndPosModelIndex {
					rep0 += lzmaBitTreeReverse(dec, specPos,
						int(rep0)-slot, direct)
				} else {
					rep0 += dec.decodeDirectBits(
						direct-lzmaNumAlignBits) << lzmaNumAlignBits
					rep0 += lzmaBitTreeReverse(dec, alignProbs, 0,
						lzmaNumAlignBits)
				}
				if rep0 == lzmaEndMarker {
					break
				}
			}
		}

		// 거리 검사는 한 곳에서만 한다 — 새 일치든 되풀이 일치든 같다.
		if int(rep0) >= len(result) {
			fail("거리가 지금까지 낸 것보다 멀다")
		}
		start := len(result) - int(rep0) - 1
		// 한 바이트씩 앞으로. 거리 1 짜리 긴 일치가 여기 기댄다.
		for j := 0; j < length; j++ {
			result = append(result, result[start+j])
		}
		if len(result) > lzmaMaxOutput {
			fail("푼 길이가 상한을 넘는다")
		}
	}

	if h.size != lzmaUnknownSize && uint64(len(result)) != h.size {
		fail("푼 길이가 머리와 다르다: %d != %d", len(result), h.size)
	}
	return result, nil
}
