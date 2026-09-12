package compresslib

// move-to-front — SPEC §4.
//
// 앞으로 **옮기는** 것이지 바꿔치는 것이 아니다. 바꿔치기도
// 자기들끼리는 왕복이 되므로, 골든 벡터가 없으면 갈라진 줄도 모른다.

const mtfAlphabet = 256

func mtfTransform(src []byte) []byte {
	var table [mtfAlphabet]byte
	for i := 0; i < mtfAlphabet; i++ {
		table[i] = byte(i)
	}
	out := make([]byte, 0, len(src))
	for _, b := range src {
		i := 0
		for table[i] != b {
			i++
		}
		out = append(out, byte(i))
		for k := i; k > 0; k-- {
			table[k] = table[k-1]
		}
		table[0] = b
	}
	return out
}

func mtfInverse(src []byte) []byte {
	var table [mtfAlphabet]byte
	for i := 0; i < mtfAlphabet; i++ {
		table[i] = byte(i)
	}
	out := make([]byte, 0, len(src))
	for _, idx := range src {
		b := table[idx]
		out = append(out, b)
		for k := int(idx); k > 0; k-- {
			table[k] = table[k-1]
		}
		table[0] = b
	}
	return out
}

func MtfEncode(src []byte) (out []byte, err error) {
	defer guard(&err)
	head := putVarint(nil, uint64(len(src)))
	return append(head, mtfTransform(src)...), nil
}

func MtfDecode(src []byte) (out []byte, err error) {
	defer guard(&err)
	n, pos := getLength(src, 0)
	if len(src)-pos != n {
		fail("몸통 길이가 헤더와 다르다: %d != %d", len(src)-pos, n)
	}
	return mtfInverse(src[pos:]), nil
}
