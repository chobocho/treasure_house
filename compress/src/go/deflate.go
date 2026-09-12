package compresslib

// DEFLATE 부호기 — SPEC §10.
//
// RFC 가 부호기에 맡긴 선택을 전부 못 박은 것이 이 파일이다. 블록
// 65535, 값을 정확히 세어 가장 작은 것, 같으면 stored → fixed →
// dynamic. 값을 어림하면 언어마다 반올림이 달라져 블록 종류가 갈린다.

const (
	dflBlockSize  = 65535
	dflHashBits   = 15
	dflHashSize   = 1 << dflHashBits
	dflChainLimit = 128
	dflNil        = -1
)

type clItem struct{ sym, value, nbits int }

func dflHash3(s []byte, i int) int {
	h := int(s[i])<<10 ^ int(s[i+1])<<5 ^ int(s[i+2])
	return h & (dflHashSize - 1)
}

func dflParse(src []byte) []lzToken {
	n := len(src)
	head := make([]int32, dflHashSize)
	for i := range head {
		head[i] = dflNil
	}
	prev := make([]int32, max(n, 1))
	for i := range prev {
		prev[i] = dflNil
	}
	insert := func(p int) {
		if p+dflMinMatch <= n {
			h := dflHash3(src, p)
			prev[p] = head[h]
			head[h] = int32(p)
		}
	}
	find := func(p int) (int, int) {
		if p+dflMinMatch > n {
			return 0, 0
		}
		bestLen, bestDist := 0, 0
		limit := dflMaxMatch
		if n-p < limit {
			limit = n - p
		}
		cand := head[dflHash3(src, p)]
		probes := 0
		for cand != dflNil && probes < dflChainLimit {
			c := int(cand)
			dist := p - c
			if dist > dflMaxDist {
				break
			}
			ln := 0
			for ln < limit && src[c+ln] == src[p+ln] {
				ln++
			}
			if ln > bestLen {
				bestLen, bestDist = ln, dist
				if ln == limit {
					break
				}
			}
			cand = prev[c]
			probes++
		}
		return bestLen, bestDist
	}

	var tokens []lzToken
	i := 0
	for i < n {
		ln, dist := find(i)
		insert(i)
		if ln >= dflMinMatch {
			nxtLen := 0
			if i+1 < n {
				nxtLen, _ = find(i + 1)
			}
			if nxtLen > ln { // 게으른 일치
				tokens = append(tokens, lzToken{false, src[i], 0, 0})
				i++
				continue
			}
			for k := 1; k < ln; k++ {
				insert(i + k)
			}
			tokens = append(tokens, lzToken{true, 0, ln, dist})
			i += ln
		} else {
			tokens = append(tokens, lzToken{false, src[i], 0, 0})
			i++
		}
	}
	return tokens
}

type dflBlock struct{ tokA, tokB, inA, inB int }

func dflSplitBlocks(tokens []lzToken) []dflBlock {
	var blocks []dflBlock
	tokStart, inStart, cur := 0, 0, 0
	for k, t := range tokens {
		if t.isMatch {
			cur += t.length
		} else {
			cur++
		}
		if cur >= dflBlockSize {
			blocks = append(blocks,
				dflBlock{tokStart, k + 1, inStart, inStart + cur})
			tokStart, inStart, cur = k+1, inStart+cur, 0
		}
	}
	if cur > 0 || len(blocks) == 0 {
		blocks = append(blocks,
			dflBlock{tokStart, len(tokens), inStart, inStart + cur})
	}
	return blocks
}

func dflFreqs(tokens []lzToken, a, b int) ([]uint64, []uint64, int) {
	lit := make([]uint64, dflLitlenSyms)
	dst := make([]uint64, dflDistSyms)
	extra := 0
	for _, t := range tokens[a:b] {
		if t.isMatch {
			code := dflLengthCode[t.length]
			lit[code]++
			extra += dflLengthExtra[code-257]
			dc := dflDistCode(t.dist)
			dst[dc]++
			extra += dflDistExtra[dc]
		} else {
			lit[t.literal]++
		}
	}
	lit[dflEndOfBlock]++
	return lit, dst, extra
}

func dflBodyBits(lit, dst []uint64, extra int,
	litLen, dstLen []int) int {
	bits := extra
	for s, f := range lit {
		if f > 0 {
			bits += int(f) * litLen[s]
		}
	}
	for s, f := range dst {
		if f > 0 {
			bits += int(f) * dstLen[s]
		}
	}
	return bits
}

// 부호 길이 배열 → (기호, 여분 값, 여분 비트). 왼쪽부터 탐욕.
func dflClEncode(lengths []int) []clItem {
	var out []clItem
	i, n := 0, len(lengths)
	for i < n {
		cur := lengths[i]
		run := 1
		for i+run < n && lengths[i+run] == cur {
			run++
		}
		if cur == 0 {
			for run >= 3 {
				var k int
				if run >= 11 {
					k = min(run, 138)
					out = append(out, clItem{dflClZeroLong, k - 11, 7})
				} else {
					k = min(run, 10)
					out = append(out, clItem{dflClZeroShort, k - 3, 3})
				}
				run -= k
				i += k
			}
			for j := 0; j < run; j++ {
				out = append(out, clItem{0, 0, 0})
				i++
			}
		} else {
			out = append(out, clItem{cur, 0, 0})
			i++
			run--
			for run >= 3 {
				k := min(run, 6)
				out = append(out, clItem{dflClRepeat, k - 3, 2})
				run -= k
				i += k
			}
			for j := 0; j < run; j++ {
				out = append(out, clItem{cur, 0, 0})
				i++
			}
		}
	}
	return out
}

func dflLastUsed(lengths []int) int {
	for s := len(lengths); s > 0; s-- {
		if lengths[s-1] > 0 {
			return s
		}
	}
	return 0
}

type dynamicPlan struct {
	litLen, dstLen, clLen       []int
	items                       []clItem
	hlit, hdist, hclen, bitCost int
}

func newDynamicPlan(litFreq, dstFreq []uint64, extra int) *dynamicPlan {
	p := &dynamicPlan{}
	p.litLen = codeLengths(litFreq, huffMaxLength)
	p.dstLen = codeLengths(dstFreq, huffMaxLength)
	any := false
	for _, l := range p.dstLen {
		if l > 0 {
			any = true
		}
	}
	if !any {
		// 일치가 하나도 없는 블록. 거리 부호를 안 보낼 수는 없으므로
		// 하나를 길이 1 로 보낸다 — 쓰이지 않는 부호다 (§10.5).
		p.dstLen[0] = 1
	}
	p.hlit = max(257, dflLastUsed(p.litLen))
	p.hdist = max(1, dflLastUsed(p.dstLen))
	joined := append(append([]int(nil), p.litLen[:p.hlit]...),
		p.dstLen[:p.hdist]...)
	p.items = dflClEncode(joined)
	clFreq := make([]uint64, dflClSyms)
	for _, it := range p.items {
		clFreq[it.sym]++
	}
	p.clLen = codeLengths(clFreq, dflClMaxLength)
	p.hclen = dflClSyms
	for p.hclen > 4 && p.clLen[dflClOrder[p.hclen-1]] == 0 {
		p.hclen--
	}
	header := 5 + 5 + 4 + 3*p.hclen
	for _, it := range p.items {
		header += p.clLen[it.sym] + it.nbits
	}
	p.bitCost = 3 + header +
		dflBodyBits(litFreq, dstFreq, extra, p.litLen, p.dstLen)
	return p
}

func dflWriteBody(w *lsbWriter, tokens []lzToken, a, b int,
	litLen, litCode, dstLen, dstCode []int) {
	for _, t := range tokens[a:b] {
		if t.isMatch {
			code := dflLengthCode[t.length]
			w.writeCode(uint64(litCode[code]), litLen[code])
			idx := code - 257
			if dflLengthExtra[idx] > 0 {
				w.writeBits(uint64(t.length-dflLengthBase[idx]),
					dflLengthExtra[idx])
			}
			dc := dflDistCode(t.dist)
			w.writeCode(uint64(dstCode[dc]), dstLen[dc])
			if dflDistExtra[dc] > 0 {
				w.writeBits(uint64(t.dist-dflDistBase[dc]),
					dflDistExtra[dc])
			}
		} else {
			w.writeCode(uint64(litCode[t.literal]), litLen[t.literal])
		}
	}
	w.writeCode(uint64(litCode[dflEndOfBlock]), litLen[dflEndOfBlock])
}

func deflateRaw(src []byte) []byte {
	var w lsbWriter
	if len(src) == 0 {
		// 마지막 고정 블록 하나, 안에는 블록 끝 기호뿐. 두 바이트 03
		// 00.
		w.writeBits(1, 1)
		w.writeBits(1, 2)
		w.writeCode(0, 7)
		w.flush()
		return w.out
	}
	tokens := dflParse(src)
	blocks := dflSplitBlocks(tokens)
	fixedCode := canonicalCodes(dflFixedLitlen)
	fixedDcode := canonicalCodes(dflFixedDist)
	for k, blk := range blocks {
		final := 0
		if k == len(blocks)-1 {
			final = 1
		}
		litFreq, dstFreq, extra := dflFreqs(tokens, blk.tokA, blk.tokB)
		rawLen := blk.inB - blk.inA
		// stored 의 값은 지금 비트 자리에 달려 있다 — 정렬 때문이다.
		pad := (8 - (w.bitPos()+3)%8) % 8
		costStored := 3 + pad + 32 + 8*rawLen
		costFixed := 3 + dflBodyBits(litFreq, dstFreq, extra,
			dflFixedLitlen, dflFixedDist)
		plan := newDynamicPlan(litFreq, dstFreq, extra)
		if costStored <= costFixed && costStored <= plan.bitCost {
			w.writeBits(uint64(final), 1)
			w.writeBits(0, 2)
			w.align()
			w.writeBits(uint64(rawLen), 16)
			w.writeBits(uint64(rawLen^0xFFFF), 16)
			for _, b := range src[blk.inA:blk.inB] {
				w.writeBits(uint64(b), 8)
			}
			continue
		}
		w.writeBits(uint64(final), 1)
		if costFixed <= plan.bitCost {
			w.writeBits(1, 2)
			dflWriteBody(&w, tokens, blk.tokA, blk.tokB, dflFixedLitlen,
				fixedCode, dflFixedDist, fixedDcode)
			continue
		}
		w.writeBits(2, 2)
		w.writeBits(uint64(plan.hlit-257), 5)
		w.writeBits(uint64(plan.hdist-1), 5)
		w.writeBits(uint64(plan.hclen-4), 4)
		for i := 0; i < plan.hclen; i++ {
			w.writeBits(uint64(plan.clLen[dflClOrder[i]]), 3)
		}
		clCode := canonicalCodes(plan.clLen)
		for _, it := range plan.items {
			w.writeCode(uint64(clCode[it.sym]), plan.clLen[it.sym])
			if it.nbits > 0 {
				w.writeBits(uint64(it.value), it.nbits)
			}
		}
		dflWriteBody(&w, tokens, blk.tokA, blk.tokB, plan.litLen,
			canonicalCodes(plan.litLen), plan.dstLen,
			canonicalCodes(plan.dstLen))
	}
	w.flush()
	return w.out
}

// 골든 코덱. 다른 모듈과 달리 varint 헤더가 없다 — 남의 형식이라 우리가
// 얹을 자리가 없고, 원본 길이는 스트림 자신이 알고 있다.
func DeflateEncode(src []byte) (out []byte, err error) {
	defer guard(&err)
	return deflateRaw(src), nil
}

func DeflateDecode(src []byte) (out []byte, err error) {
	defer guard(&err)
	return inflateRaw(src), nil
}
