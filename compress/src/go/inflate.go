package compresslib

// inflate — RFC 1951 복호기 (SPEC §10.7).
//
// 부호기보다 복호기가 먼저다. 형식을 읽을 줄 알아야 내가 쓴 것이 맞는지
// 알 수 있고, 무엇보다 진짜 gzip 이 만든 파일을 풀 수 있어야 한다.
//
// 예외 하나: 거리 부호가 하나뿐인 표는 크래프트 합이 1/2 라 "모자란"
// 표인데, RFC 가 허용하고 zlib 도 낸다. 일치 없는 블록에서 나온다.

func inflateTable(lengths []int) *huffDecoder {
	checkComplete(lengths)
	return newHuffDecoder(lengths)
}

func inflateBody(r *lsbReader, out []byte,
	litlen, dist *huffDecoder) []byte {
	for {
		sym := litlen.read(r)
		if sym < 256 {
			out = append(out, byte(sym))
			continue
		}
		if sym == dflEndOfBlock {
			return out
		}
		idx := sym - 257
		if idx >= len(dflLengthBase) {
			fail("길이 부호 %d 는 없다", sym)
		}
		length := dflLengthBase[idx] +
			int(r.readBits(dflLengthExtra[idx]))
		dcode := dist.read(r)
		if dcode >= dflDistSyms {
			fail("거리 부호 %d 는 쓰이지 않는다", dcode)
		}
		d := dflDistBase[dcode] + int(r.readBits(dflDistExtra[dcode]))
		if d > len(out) {
			fail("거리 %d 가 지금까지 낸 것보다 멀다", d)
		}
		start := len(out) - d
		// 한 바이트씩 앞으로. 거리 1 짜리 긴 일치가 여기 기댄다.
		for k := 0; k < length; k++ {
			out = append(out, out[start+k])
		}
	}
}

func inflateDynamic(r *lsbReader) (*huffDecoder, *huffDecoder) {
	hlit := int(r.readBits(5)) + 257
	hdist := int(r.readBits(5)) + 1
	hclen := int(r.readBits(4)) + 4
	if hlit > dflLitlenSyms || hdist > dflDistSyms {
		fail("HLIT/HDIST 가 알파벳을 넘는다")
	}
	clLengths := make([]int, dflClSyms)
	for i := 0; i < hclen; i++ {
		clLengths[dflClOrder[i]] = int(r.readBits(3))
	}
	cl := inflateTable(clLengths)

	want := hlit + hdist
	lengths := make([]int, 0, want)
	for len(lengths) < want {
		sym := cl.read(r)
		switch {
		case sym < 16:
			lengths = append(lengths, sym)
		case sym == dflClRepeat:
			if len(lengths) == 0 {
				fail("부호 16 이 맨 앞에 왔다")
			}
			prev := lengths[len(lengths)-1]
			for i := int(r.readBits(2)) + 3; i > 0; i-- {
				lengths = append(lengths, prev)
			}
		case sym == dflClZeroShort:
			for i := int(r.readBits(3)) + 3; i > 0; i-- {
				lengths = append(lengths, 0)
			}
		default:
			for i := int(r.readBits(7)) + 11; i > 0; i-- {
				lengths = append(lengths, 0)
			}
		}
	}
	if len(lengths) != want {
		fail("부호 길이 되풀이가 표 끝을 넘었다")
	}
	return inflateTable(lengths[:hlit]), inflateTable(lengths[hlit:])
}

func inflateRaw(src []byte) []byte {
	r := &lsbReader{src: src}
	var out []byte
	var fixedLit, fixedDst *huffDecoder
	for {
		final := r.readBit()
		btype := int(r.readBits(2))
		switch btype {
		case 0:
			r.align()
			p := r.pos
			if p+4 > len(src) {
				fail("stored 블록 머리가 잘렸다")
			}
			ln := int(src[p]) | int(src[p+1])<<8
			nln := int(src[p+2]) | int(src[p+3])<<8
			p += 4
			if ln != nln^0xFFFF {
				fail("NLEN 이 LEN 의 보수가 아니다")
			}
			if p+ln > len(src) {
				fail("stored 블록 몸통이 잘렸다")
			}
			out = append(out, src[p:p+ln]...)
			r.pos = p + ln
		case 1:
			if fixedLit == nil {
				fixedLit = inflateTable(dflFixedLitlen)
				fixedDst = inflateTable(dflFixedDist)
			}
			out = inflateBody(r, out, fixedLit, fixedDst)
		case 2:
			lit, dst := inflateDynamic(r)
			out = inflateBody(r, out, lit, dst)
		default:
			fail("BTYPE 11 은 없는 블록 종류다")
		}
		if final != 0 {
			return out
		}
	}
}

func InflateRaw(src []byte) (out []byte, err error) {
	defer guard(&err)
	return inflateRaw(src), nil
}
