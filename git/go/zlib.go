package mygit

// zlib 겉옷 (SPEC.md §3) — 느슨한 객체와 팩 항목이 입는 옷.
//
// Go 는 표준 compress/zlib 을 쓴다(SPEC.md §3.1 의 표). 팩 안에서는
// "스트림이 몇 바이트에서 끝나는가" 가 필요한데, flate 는 입력이
// io.ByteReader 이면 버퍼를 끼우지 않고 한 바이트씩 읽는다. 그래서
// bytes.Reader 를 주고 다 읽은 뒤 남은 길이를 빼면 먹은 수가 나온다.

import (
	"bytes"
	"compress/zlib"
	"hash/adler32"
	"io"
)

// Level 은 git 의 느슨한 객체 기본값과 같은 "가장 빠르게".
const Level = 1

func Compress(data []byte) []byte {
	var buf bytes.Buffer
	w, _ := zlib.NewWriterLevel(&buf, Level)
	w.Write(data)
	w.Close()
	return buf.Bytes()
}

// DecompressPrefix 는 data[start:] 에서 스트림 하나를 풀어 (바이트,
// 먹은 수). 먹은 수에는 머리 2바이트와 Adler-32 꼬리 4바이트가
// 들어간다. O(스트림 길이).
func DecompressPrefix(data []byte, start int) ([]byte, int, error) {
	r := bytes.NewReader(data[start:])
	z, err := zlib.NewReader(r)
	if err != nil {
		return nil, 0, Fail("fatal: mygit: corrupt zlib stream")
	}
	out, err := io.ReadAll(z)
	if err == io.ErrUnexpectedEOF {
		return nil, 0, Fail("fatal: mygit: truncated zlib stream")
	}
	if err != nil {
		return nil, 0, Fail("fatal: mygit: corrupt zlib stream")
	}
	return out, len(data) - start - r.Len(), nil
}

// Decompress 는 스트림 하나를 끝까지. 뒤에 남는 바이트가 있으면
// 오류다.
func Decompress(data []byte) ([]byte, error) {
	out, used, err := DecompressPrefix(data, 0)
	if err != nil {
		return nil, err
	}
	if used != len(data) {
		return nil, Fail("fatal: mygit: garbage after zlib stream")
	}
	return out, nil
}

func Adler32(data []byte) uint32 { return adler32.Checksum(data) }
