package compresslib

// 정수 부호 — SPEC §2.
//
// varint 만 바이트 단위이고 감마·델타·라이스는 비트 스트림(MSB
// 먼저)에서 돈다. 단항은 **1 을 q개 쓰고 0 으로 닫는다** — 반대 약속도
// 문헌에 흔한데, 섞어 쓰면 작은 값은 그대로 왕복돼서 골든 벡터 전에는
// 안 보인다.

import "math/bits"

// 단항 상한 (SPEC §2.5). 손상된 파일이 무한 루프가 되지 않게 하되,
// k=0 인 라이스(= 순수 단항)가 쓸모 있을 만큼은 크게.
const maxUnary = 4096

func zigzag(n int64) uint64 { return uint64(n<<1) ^ uint64(n>>63) }

func unzigzag(u uint64) int64 { return int64(u>>1) ^ -int64(u&1) }

func putGamma(w *msbWriter, v uint64) {
	if v < 1 {
		fail("gamma 는 1 이상만: %d", v)
	}
	n := bits.Len64(v)
	w.writeBits(0, n-1)
	w.writeBits(v, n)
}

func getGamma(r *msbReader) uint64 {
	n := 1
	for r.readBit() == 0 {
		n++
		if n > 64 {
			fail("gamma 의 길이 부분이 64비트를 넘는다")
		}
	}
	return uint64(1)<<uint(n-1) | r.readBits(n-1)
}

func putDelta(w *msbWriter, v uint64) {
	if v < 1 {
		fail("delta 는 1 이상만: %d", v)
	}
	n := bits.Len64(v)
	putGamma(w, uint64(n))
	w.writeBits(v, n-1)
}

func getDelta(r *msbReader) uint64 {
	n := getGamma(r)
	if n > 64 {
		fail("delta 의 길이 부분이 64비트를 넘는다")
	}
	return uint64(1)<<uint(n-1) | r.readBits(int(n)-1)
}

func putRice(w *msbWriter, v uint64, k int) {
	q := v >> uint(k)
	if q > maxUnary {
		fail("rice 의 몫이 %d — k 를 잘못 골랐다", q)
	}
	for i := uint64(0); i < q; i++ {
		w.writeBit(1)
	}
	w.writeBit(0)
	if k > 0 {
		w.writeBits(v&(uint64(1)<<uint(k)-1), k)
	}
}

func getRice(r *msbReader, k int) uint64 {
	var q uint64
	for r.readBit() == 1 {
		q++
		if q > maxUnary {
			fail("rice 의 단항이 %d 를 넘는다", maxUnary)
		}
	}
	if k == 0 {
		return q
	}
	return q<<uint(k) | r.readBits(k)
}

// 골든 코덱 (SPEC §2.6) — 바이트마다 gamma(b+1).
func IntcodeEncode(src []byte) (out []byte, err error) {
	defer guard(&err)
	var w msbWriter
	for _, b := range src {
		putGamma(&w, uint64(b)+1)
	}
	w.flush()
	return append(putVarint(nil, uint64(len(src))), w.out...), nil
}

func IntcodeDecode(src []byte) (out []byte, err error) {
	defer guard(&err)
	n, pos := getLength(src, 0)
	r := msbReader{src: src, pos: pos}
	result := make([]byte, 0, n)
	for i := 0; i < n; i++ {
		v := getGamma(&r) - 1
		if v > 255 {
			fail("바이트 범위를 벗어난 값: %d", v)
		}
		result = append(result, byte(v))
	}
	return result, nil
}
