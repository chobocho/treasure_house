package compresslib

// zlib 과 gzip 컨테이너 — SPEC §10.8 (RFC 1950, RFC 1952).
//
// gzip 머리의 MTIME 을 **0 으로 못 박는다.** 진짜 gzip 은 파일의 수정
// 시각을 적어서 같은 입력에 같은 바이트가 안 나온다 — 재현이 안 된다.
// 우리는 make record 를 세 번 돌려 md5 가 같아야 하므로 0 을 쓴다.

const (
	zlibCMF = 0x78 // CM 8 = deflate, CINFO 7 = 32 KiB 창
	// FDICT 0, FLEVEL 2, 그리고 (CMF<<8|FLG) 가 31 의 배수
	zlibFLG       = 0x9C
	gzipDeflate   = 8
	gzipOsUnknown = 255
)

func ZlibCompress(src []byte) (out []byte, err error) {
	defer guard(&err)
	result := []byte{zlibCMF, zlibFLG}
	result = append(result, deflateRaw(src)...)
	a := adler32(src)
	return append(result,
		byte(a>>24), byte(a>>16), byte(a>>8), byte(a)), nil
}

func ZlibDecompress(src []byte) (out []byte, err error) {
	defer guard(&err)
	if len(src) < 6 {
		fail("zlib 스트림이 너무 짧다")
	}
	cmf, flg := int(src[0]), int(src[1])
	if cmf&0x0F != 8 {
		fail("zlib CM 이 8 이 아니다: %d", cmf&0x0F)
	}
	if (cmf<<8|flg)%31 != 0 {
		fail("zlib 머리의 검사식이 31 로 안 나눠진다")
	}
	if flg&0x20 != 0 {
		fail("미리 정한 사전(FDICT)은 지원하지 않는다")
	}
	result := inflateRaw(src[2 : len(src)-4])
	tail := src[len(src)-4:]
	want := uint32(tail[0])<<24 | uint32(tail[1])<<16 |
		uint32(tail[2])<<8 | uint32(tail[3])
	if adler32(result) != want {
		fail("Adler-32 가 다르다")
	}
	return result, nil
}

func GzipCompress(src []byte) (out []byte, err error) {
	defer guard(&err)
	result := []byte{0x1F, 0x8B, gzipDeflate, 0,
		0, 0, 0, 0, 0, gzipOsUnknown}
	result = append(result, deflateRaw(src)...)
	c := crc32of(src)
	n := uint32(len(src))
	result = append(result,
		byte(c), byte(c>>8), byte(c>>16), byte(c>>24))
	return append(result,
		byte(n), byte(n>>8), byte(n>>16), byte(n>>24)), nil
}

func GzipDecompress(src []byte) (out []byte, err error) {
	defer guard(&err)
	if len(src) < 18 {
		fail("gzip 스트림이 너무 짧다")
	}
	if src[0] != 0x1F || src[1] != 0x8B {
		fail("gzip 매직이 아니다")
	}
	if src[2] != gzipDeflate {
		fail("gzip CM 이 8 이 아니다: %d", src[2])
	}
	flg := src[3]
	pos := 10
	if flg&0x04 != 0 { // FEXTRA
		pos += 2 + int(src[pos]) | int(src[pos+1])<<8
	}
	for _, bit := range []byte{0x08, 0x10} { // FNAME, FCOMMENT
		if flg&bit != 0 {
			for pos < len(src) && src[pos] != 0 {
				pos++
			}
			pos++
		}
	}
	if flg&0x02 != 0 { // FHCRC
		pos += 2
	}
	if pos+8 >= len(src) {
		fail("gzip 머리가 잘렸다")
	}
	result := inflateRaw(src[pos : len(src)-8])
	tail := src[len(src)-8:]
	crc := uint32(tail[0]) | uint32(tail[1])<<8 |
		uint32(tail[2])<<16 | uint32(tail[3])<<24
	size := uint32(tail[4]) | uint32(tail[5])<<8 |
		uint32(tail[6])<<16 | uint32(tail[7])<<24
	if crc32of(result) != crc {
		fail("CRC-32 가 다르다")
	}
	if uint32(len(result)) != size {
		fail("ISIZE 가 푼 길이와 다르다")
	}
	return result, nil
}
