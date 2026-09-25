// 슬라이드 p7-v121-wasip1 — GOOS=wasip1 일 때만 빌드, Go 1.21
package main

// hostRandom is provided by the WebAssembly host (WASI preview 1).
//
//go:wasmimport wasi_snapshot_preview1 random_get
func hostRandom(buf *byte, n uint32) uint32

func where() string {
	var b byte
	hostRandom(&b, 1)
	return "wasip1 (host gave a random byte)"
}
