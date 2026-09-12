package compresslib

// Go 시험 — go test ./src/go/ 로 돈다.
//
// 파이썬 쪽보다 얇다. 진짜 문지기는 파서티 검사(골든 대조 + 5×5 교차
// 복호) 이고, 여기서는 그 검사가 못 보는 것만 본다 — 오류를 내야 할
// 자리에서 진짜 내는가, 그리고 명세의 표가 이 언어에서도 그대로
// 나오는가.

import (
	"bytes"
	"testing"
)

func pseudo(n int, a, c int) []byte {
	out := make([]byte, n)
	for i := range out {
		out[i] = byte((i*a + c) & 0xFF)
	}
	return out
}

func repeat(b byte, n int) []byte { return bytes.Repeat([]byte{b}, n) }

func mustEq(t *testing.T, got, want []byte, what string) {
	t.Helper()
	if !bytes.Equal(got, want) {
		t.Fatalf("%s: %v != %v", what, got, want)
	}
}

func TestBitio(t *testing.T) {
	var w msbWriter
	w.writeBit(1)
	w.flush()
	mustEq(t, w.out, []byte{0x80}, "첫 비트는 7번 비트에")

	var w2 msbWriter
	w2.writeBits(0b111, 3)
	w2.flush()
	mustEq(t, w2.out, []byte{0xE0}, "채움은 0 이다")

	var w3 lsbWriter // 빈 DEFLATE 스트림
	w3.writeBits(1, 1)
	w3.writeBits(1, 2)
	w3.writeCode(0, 7)
	w3.flush()
	mustEq(t, w3.out, []byte{0x03, 0x00}, "빈 DEFLATE")

	out, _ := BitioEncode(nil)
	mustEq(t, out, []byte{0x00, 0x00}, "빈 입력")
}

func TestIntcode(t *testing.T) {
	mustEq(t, putVarint(nil, 300), []byte{0xAC, 0x02}, "varint(300)")
	for _, n := range []int64{-1 << 63, 1<<63 - 1, 0, -1, 1} {
		if unzigzag(zigzag(n)) != n {
			t.Fatalf("zigzag 왕복 실패: %d", n)
		}
	}
	var w msbWriter
	putGamma(&w, 4) // 00100
	w.flush()
	mustEq(t, w.out, []byte{0x20}, "gamma(4)")
}

func TestRle(t *testing.T) {
	out, _ := RleEncode([]byte("AAA"))
	mustEq(t, out, []byte{0x03, 0xFE, 'A'}, "런 3")
	out, _ = RleEncode([]byte("AB"))
	mustEq(t, out, []byte{0x02, 0x01, 'A', 'B'}, "리터럴 둘")
	out, _ = RleEncode(repeat('A', 128))
	mustEq(t, out, []byte{0x80, 0x01, 0x81, 'A'}, "런 상한 128")
	if _, err := RleDecode([]byte{0x03, 0x80, 'A', 'A', 'A'}); err == nil {
		t.Fatal("제어 128 을 받아들였다")
	}
	zeros := []int{0, 0, 0}
	got := zeroRunEncode(zeros)
	if len(got) != 2 || got[0] != 0 || got[1] != 0 {
		t.Fatalf("0런 3 = RUNA,RUNA 여야 한다: %v", got)
	}
}

func TestMtf(t *testing.T) {
	mustEq(t, mtfTransform([]byte("AAAA")), []byte{'A', 0, 0, 0}, "되풀이")
	// 옮기는 것이지 바꿔치는 것이 아니다 — 바꿔치기면 마지막이 0 이
	// 된다
	mustEq(t, mtfTransform([]byte("CBAB")), []byte{'C', 'C', 'C', 1}, "옮기기")
}

func TestHuffman(t *testing.T) {
	f := make([]uint64, 256)
	f[0], f[1], f[2] = 5, 2, 1
	l := codeLengths(f, huffMaxLength)
	if l[0] != 1 || l[1] != 2 || l[2] != 2 {
		t.Fatalf("5,2,1 → 1,2,2 여야 한다: %v", l[:3])
	}
	g := make([]uint64, 256)
	for i := 0; i < 7; i++ {
		g[i] = 1
	}
	l7 := codeLengths(g, huffMaxLength)
	if l7[0] != 3 || l7[5] != 3 || l7[6] != 2 {
		t.Fatalf("같은 빈도 일곱: %v", l7[:7])
	}
	// RFC 1951 §3.2.2 의 예
	rfc := make([]int, 256)
	copy(rfc, []int{3, 3, 3, 3, 3, 2, 4, 4})
	codes := canonicalCodes(rfc)
	if codes[0] != 0b010 || codes[5] != 0b00 || codes[7] != 0b1111 {
		t.Fatalf("캐노니컬 부호: %v", codes[:8])
	}
}

func TestLzss(t *testing.T) {
	out, _ := LzssEncode([]byte("A"))
	mustEq(t, out, []byte{0x01, 0x00, 'A'}, "리터럴 하나")
	out, _ = LzssEncode([]byte("AAAA"))
	mustEq(t, out, []byte{0x04, 0x40, 'A', 0x00, 0x00, 0x00}, "첫 일치")
	// 거리 1 짜리 긴 일치 — copy 로 한 번에 옮기면 여기서 깨진다
	run := repeat('A', 1000)
	enc, _ := LzssEncode(run)
	dec, _ := LzssDecode(enc)
	mustEq(t, dec, run, "겹치는 일치")
	if _, err := LzssDecode([]byte{0x03, 0x80, 0x00, 0x01, 0x00}); err == nil {
		t.Fatal("시작보다 먼 거리를 받아들였다")
	}
}

func TestLzw(t *testing.T) {
	out, _ := LzwEncode([]byte("A"))
	mustEq(t, out, []byte{0x01, 0x20, 0xC0, 0x40}, "한 바이트")
	// 사전이 두 번 넘게 꽉 차는 크기 — 폭 확장의 한 칸 지연을 밟는다
	big := pseudo(200000, 131, 7)
	enc, _ := LzwEncode(big)
	dec, err := LzwDecode(enc)
	if err != nil {
		t.Fatal(err)
	}
	mustEq(t, dec, big, "사전 되감기")
}

func TestRangecoder(t *testing.T) {
	src := pseudo(1000, 37, 11)
	out, _ := RangecoderEncode(src)
	head := len(putVarint(nil, uint64(len(src))))
	if out[head] != 0 {
		t.Fatal("코더 스트림의 첫 바이트는 늘 0 이다")
	}
	dec, _ := RangecoderDecode(out)
	mustEq(t, dec, src, "왕복")
	bad := append([]byte(nil), out...)
	bad[head] = 1
	if _, err := RangecoderDecode(bad); err == nil {
		t.Fatal("첫 바이트가 0 이 아닌 스트림을 받아들였다")
	}
}

func TestBwt(t *testing.T) {
	l, primary := bwtTransformBlock([]byte("banana"))
	mustEq(t, l, []byte("nnbaaa"), "banana 의 L 열")
	if primary != 3 {
		t.Fatalf("primary 는 3 이어야 한다: %d", primary)
	}
	mustEq(t, bwtInverseBlock(l, primary), []byte("banana"), "역변환")
	// 모든 회전이 같다 — 동점은 시작 위치 오름차순이라 primary 가 0
	_, p2 := bwtTransformBlock(repeat(0, 64))
	if p2 != 0 {
		t.Fatalf("동점 규칙: primary 가 0 이어야 한다: %d", p2)
	}
}

func TestDeflate(t *testing.T) {
	out, _ := DeflateEncode(nil)
	mustEq(t, out, []byte{0x03, 0x00}, "빈 입력")
	if _, err := InflateRaw([]byte{0x07, 0x00}); err == nil {
		t.Fatal("BTYPE 11 을 받아들였다")
	}
	bad := []byte{0x01, 0x01, 0x00, 0x00, 0x00, 'A'}
	if _, err := InflateRaw(bad); err == nil {
		t.Fatal("NLEN 이 틀린 stored 블록을 받아들였다")
	}
	src := pseudo(50000, 37, 11)
	enc, _ := DeflateEncode(src)
	dec, _ := DeflateDecode(enc)
	mustEq(t, dec, src, "왕복")
	gz, _ := GzipCompress([]byte("hi"))
	if gz[4] != 0 || gz[5] != 0 || gz[6] != 0 || gz[7] != 0 {
		t.Fatal("MTIME 은 0 이어야 재현된다")
	}
	broken := append([]byte(nil), gz...)
	broken[len(broken)-5] ^= 0xFF
	if _, err := GzipDecompress(broken); err == nil {
		t.Fatal("CRC 가 틀린 gzip 을 받아들였다")
	}
}

func TestRoundTrips(t *testing.T) {
	cases := [][]byte{nil, []byte("A"), repeat(0, 5000),
		pseudo(20000, 37, 11), pseudo(70000, 131, 3)}
	for _, e := range Entries {
		for _, src := range cases {
			enc, err := e.Encode(src)
			if err != nil {
				t.Fatalf("%s 부호화 실패: %v", e.Name, err)
			}
			dec, err := e.Decode(enc)
			if err != nil {
				t.Fatalf("%s 복호 실패: %v", e.Name, err)
			}
			if !bytes.Equal(dec, src) && !(len(dec) == 0 && len(src) == 0) {
				t.Fatalf("%s 왕복 실패 (%d 바이트)", e.Name, len(src))
			}
		}
	}
}
