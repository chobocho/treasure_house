package input

import "testing"

// 파서는 키 하나마다 불린다. 사람이 아무리 빨리 쳐도 초당 스무 번을 넘기 어려우니
// 여유는 충분하지만, 붙여넣기는 한 번에 수만 바이트가 오기도 한다.
//
//	go test -bench . -benchmem ./input/

func BenchmarkDecodeASCII(b *testing.B) {
	p := []byte("hello world")
	for i := 0; i < b.N; i++ {
		var d Decoder
		_ = d.Feed(p)
	}
}

func BenchmarkDecodeArrow(b *testing.B) {
	p := []byte("\x1b[A")
	for i := 0; i < b.N; i++ {
		var d Decoder
		_ = d.Feed(p)
	}
}

func BenchmarkDecodeHangul(b *testing.B) {
	p := []byte("보리차 한 잔")
	for i := 0; i < b.N; i++ {
		var d Decoder
		_ = d.Feed(p)
	}
}

func BenchmarkDecodeMouse(b *testing.B) {
	p := []byte("\x1b[<0;120;40M")
	for i := 0; i < b.N; i++ {
		var d Decoder
		_ = d.Feed(p)
	}
}

// 4 KB 짜리 붙여넣기 한 번.
func BenchmarkDecodePaste(b *testing.B) {
	body := make([]byte, 4096)
	for i := range body {
		body[i] = 'x'
	}
	p := append(append([]byte("\x1b[200~"), body...), "\x1b[201~"...)
	b.SetBytes(int64(len(p)))
	for i := 0; i < b.N; i++ {
		var d Decoder
		_ = d.Feed(p)
	}
}
