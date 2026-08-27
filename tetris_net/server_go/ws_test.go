package main

// ws_test.go — 직접 구현한 RFC 6455 코덱을 net.Pipe() 위에서 검증한다.
// 네트워크가 필요 없다. 프레임 규격은 바이트 배열 문제이지 통신 문제가 아니다.
import (
	"bytes"
	"io"
	"net"
	"strings"
	"testing"
	"time"
)

// RFC 6455 §1.3 에 그대로 실린 예제. 이 한 줄이 맞으면 핸드셰이크는 맞는 것이다.
func TestAcceptKey(t *testing.T) {
	got := AcceptKey("dGhlIHNhbXBsZSBub25jZQ==")
	if want := "s3pPLMBiTxaQ9kYGzzhZRbK+xOo="; got != want {
		t.Fatalf("Sec-WebSocket-Accept: 기대 %q, 실제 %q", want, got)
	}
}

// 서버 쪽 Conn 을 만들고, 반대편에서 "클라이언트처럼" 마스킹한 프레임을 밀어 넣는다.
func pair(t *testing.T) (*Conn, net.Conn) {
	t.Helper()
	a, b := net.Pipe()
	// net.Pipe 는 버퍼가 없어서 한쪽이 멈추면 반대쪽도 영원히 멈춘다.
	// 마감을 걸어 두면 구현이 덜 됐을 때 테스트가 매달리지 않고 실패한다.
	dl := time.Now().Add(3 * time.Second)
	a.SetDeadline(dl)
	b.SetDeadline(dl)
	t.Cleanup(func() { a.Close(); b.Close() })
	return NewConn(a), b
}

func TestReadMaskedText(t *testing.T) {
	srv, cli := pair(t)
	go func() {
		WriteFrame(cli, OpText, []byte("안녕 8인 대전"), true)
		cli.Close()
	}()
	op, data, err := srv.ReadMessage()
	if err != nil {
		t.Fatalf("읽기 실패: %v", err)
	}
	if op != OpText || string(data) != "안녕 8인 대전" {
		t.Fatalf("op=%d data=%q", op, data)
	}
}

// 클라이언트 프레임은 반드시 마스킹돼야 한다 (RFC 6455 §5.1). 아니면 끊는다.
func TestRejectUnmasked(t *testing.T) {
	srv, cli := pair(t)
	go func() { WriteFrame(cli, OpText, []byte("hi"), false); cli.Close() }()
	if _, _, err := srv.ReadMessage(); err == nil {
		t.Fatal("마스킹 없는 클라이언트 프레임은 거절해야 한다")
	}
}

// 조각난 메시지 — 첫 조각은 opcode, 나머지는 continuation(0), 마지막에 FIN.
func TestFragmented(t *testing.T) {
	srv, cli := pair(t)
	go func() {
		writeRaw(cli, false, OpText, []byte("가"), true)
		writeRaw(cli, false, OpCont, []byte("나"), true)
		writeRaw(cli, true, OpCont, []byte("다"), true)
		cli.Close()
	}()
	op, data, err := srv.ReadMessage()
	if err != nil || op != OpText || string(data) != "가나다" {
		t.Fatalf("조각 이어붙이기 실패: op=%d data=%q err=%v", op, data, err)
	}
}

// 핑이 오면 같은 페이로드로 퐁을 돌려주고, 그 프레임은 애플리케이션에 올리지 않는다.
func TestPingAutoPong(t *testing.T) {
	srv, cli := pair(t)
	done := make(chan []byte, 1)
	go func() {
		WriteFrame(cli, OpPing, []byte("ka"), true)
		buf := make([]byte, 64)
		n, _ := cli.Read(buf)
		done <- buf[:n]
		WriteFrame(cli, OpText, []byte("ok"), true)
	}()
	op, data, err := srv.ReadMessage()
	if err != nil || op != OpText || string(data) != "ok" {
		t.Fatalf("핑 뒤의 본문을 못 읽었다: op=%d %q %v", op, data, err)
	}
	pong := <-done
	if len(pong) < 2 || pong[0] != 0x80|OpPong || !bytes.Contains(pong, []byte("ka")) {
		t.Fatalf("퐁 프레임이 아니다: %v", pong)
	}
}

// 길이 인코딩 세 갈래 — 7비트 / 16비트 / 64비트
func TestLengthEncoding(t *testing.T) {
	for _, n := range []int{0, 125, 126, 65535, 65536} {
		srv, cli := pair(t)
		payload := bytes.Repeat([]byte("x"), n)
		go func() { WriteFrame(cli, OpBinary, payload, true); cli.Close() }()
		op, data, err := srv.ReadMessage()
		if err != nil || op != OpBinary || len(data) != n {
			t.Fatalf("%d바이트 왕복 실패: op=%d len=%d err=%v", n, op, len(data), err)
		}
	}
}

// 닫기 프레임을 받으면 EOF 로 끝난다.
func TestClose(t *testing.T) {
	srv, cli := pair(t)
	go func() { WriteFrame(cli, OpClose, []byte{0x03, 0xe8}, true); cli.Close() }()
	if _, _, err := srv.ReadMessage(); err != io.EOF {
		t.Fatalf("닫기 프레임 뒤에는 EOF 여야 한다: %v", err)
	}
}

// 서버가 내보내는 프레임은 마스킹하지 않는다 (RFC 6455 §5.1).
func TestServerWriteUnmasked(t *testing.T) {
	srv, cli := pair(t)
	go func() { srv.WriteText([]byte("hello")) }()
	buf := make([]byte, 32)
	n, _ := cli.Read(buf)
	if n < 2 || buf[1]&0x80 != 0 {
		t.Fatalf("서버 프레임에 마스크 비트가 켜져 있다: %v", buf[:n])
	}
	if !strings.Contains(string(buf[:n]), "hello") {
		t.Fatalf("본문이 안 보인다: %q", buf[:n])
	}
}

// 너무 큰 프레임은 읽지 않고 끊는다 — 메모리를 지키는 유일한 장치다.
func TestMaxPayload(t *testing.T) {
	srv, cli := pair(t)
	srv.MaxPayload = 16
	go func() { WriteFrame(cli, OpText, bytes.Repeat([]byte("y"), 64), true); cli.Close() }()
	if _, _, err := srv.ReadMessage(); err == nil {
		t.Fatal("상한을 넘는 프레임은 거절해야 한다")
	}
}
