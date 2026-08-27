package main

// ws.go — WebSocket(RFC 6455) 서버 쪽을 직접 구현한다. 외부 패키지를 쓰지 않는다.
//
// 왜 직접 쓰나: 이 문서가 가르치려는 것 중 하나가 "웹소켓은 대단한 프로토콜이 아니다"라는
// 사실이다. 핸드셰이크는 SHA-1 한 번이고, 프레임은 2바이트 머리 + 길이 + (마스크) + 본문이다.
// 아래 200줄이 그 전부다. 게다가 의존성이 0이면 `go build` 하나로 단일 바이너리가 나온다.
//
// 다루지 않는 것: 확장(permessage-deflate), 서브프로토콜 협상, 클라이언트 쪽 Dial.
// 이 게임에 필요 없다. 필요해지면 그때 넣으면 된다.

import (
	"bufio"
	"crypto/rand"
	"crypto/sha1"
	"encoding/base64"
	"encoding/binary"
	"errors"
	"fmt"
	"io"
	"net"
	"net/http"
	"net/url"
	"strings"
	"sync"
	"time"
)

// 프레임 종류 (RFC 6455 §5.2). 상위 비트(0x8)가 켜져 있으면 제어 프레임이다.
const (
	OpCont   byte = 0x0
	OpText   byte = 0x1
	OpBinary byte = 0x2
	OpClose  byte = 0x8
	OpPing   byte = 0x9
	OpPong   byte = 0xA
)

// RFC 6455 §1.3 이 못 박아 둔 마법 문자열. 이 값 때문에 캐시나 프록시가
// 핸드셰이크 응답을 "그냥 HTTP 응답"으로 착각해 재사용하지 못한다.
const wsGUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

// AcceptKey — 클라이언트가 보낸 Sec-WebSocket-Key 에서 응답 헤더 값을 만든다.
// base64(SHA1(key + GUID)). 암호학적 의미는 없고, "나는 웹소켓을 아는 서버다"라는 증표다.
func AcceptKey(key string) string {
	h := sha1.New()
	io.WriteString(h, key)
	io.WriteString(h, wsGUID)
	return base64.StdEncoding.EncodeToString(h.Sum(nil))
}

// Conn — 업그레이드가 끝난 연결 하나.
type Conn struct {
	c          net.Conn
	br         *bufio.Reader
	wmu        sync.Mutex // 쓰기는 프레임 단위로 원자적이어야 한다. 여러 고루틴이 같이 쓴다
	MaxPayload int64      // 한 메시지의 상한. 이 게임의 최대 메시지는 1KB 도 안 된다
	Client     bool       // 클라이언트 쪽이면 방향이 뒤집힌다 (보낼 때 마스킹, 받을 때 요구 안 함)
	closed     bool
}

func NewConn(c net.Conn) *Conn { return newConn(c, bufio.NewReader(c)) }
func newConn(c net.Conn, br *bufio.Reader) *Conn {
	return &Conn{c: c, br: br, MaxPayload: 1 << 20}
}

// Upgrade — HTTP 요청 하나를 WebSocket 연결로 바꾼다.
// http.Hijacker 로 소켓을 통째로 빼앗아 오는 게 핵심이다. 그 뒤로는 net/http 가
// 이 연결에 손을 대지 않으므로 우리가 프레임을 직접 읽고 쓸 수 있다.
func Upgrade(w http.ResponseWriter, r *http.Request) (*Conn, error) {
	if !strings.EqualFold(r.Header.Get("Upgrade"), "websocket") {
		return nil, errors.New("Upgrade 헤더가 websocket 이 아니다")
	}
	if !strings.Contains(strings.ToLower(r.Header.Get("Connection")), "upgrade") {
		return nil, errors.New("Connection 헤더에 upgrade 가 없다")
	}
	if r.Header.Get("Sec-WebSocket-Version") != "13" {
		return nil, errors.New("Sec-WebSocket-Version 이 13 이 아니다")
	}
	key := r.Header.Get("Sec-WebSocket-Key")
	if key == "" {
		return nil, errors.New("Sec-WebSocket-Key 가 없다")
	}
	hj, ok := w.(http.Hijacker)
	if !ok {
		return nil, errors.New("이 ResponseWriter 는 Hijack 을 지원하지 않는다")
	}
	c, brw, err := hj.Hijack()
	if err != nil {
		return nil, err
	}
	// 101 을 손으로 쓴다. 여기서부터는 HTTP 가 아니다.
	_, err = fmt.Fprintf(brw, "HTTP/1.1 101 Switching Protocols\r\n"+
		"Upgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Accept: %s\r\n\r\n", AcceptKey(key))
	if err == nil {
		err = brw.Flush()
	}
	if err != nil {
		c.Close()
		return nil, err
	}
	// 하이재킹으로 받은 bufio.Reader 를 그대로 써야 한다.
	// 클라이언트가 101 을 기다리지 않고 첫 프레임을 붙여 보냈다면 그게 여기 들어 있다.
	return newConn(c, brw.Reader), nil
}

// ── 프레임 쓰기 ──
// 머리와 본문을 **한 번에** 쓴다. 두 번 나눠 쓰면 작은 프레임이 두 개의 TCP 세그먼트로
// 쪼개져 나가고, 상대가 헤더만 읽고 멈추는 상황이 생긴다(테스트가 이걸 잡는다).
func writeRaw(w io.Writer, fin bool, op byte, p []byte, mask bool) error {
	n := 2
	l := len(p)
	var head [14]byte
	head[0] = op & 0x0f
	if fin {
		head[0] |= 0x80
	}
	switch {
	case l < 126:
		head[1] = byte(l)
	case l <= 0xffff:
		head[1] = 126
		binary.BigEndian.PutUint16(head[2:], uint16(l))
		n = 4
	default:
		head[1] = 127
		binary.BigEndian.PutUint64(head[2:], uint64(l))
		n = 10
	}
	var key [4]byte
	if mask {
		head[1] |= 0x80
		if _, err := rand.Read(key[:]); err != nil {
			return err
		}
		copy(head[n:], key[:])
		n += 4
	}
	buf := make([]byte, n+l)
	copy(buf, head[:n])
	copy(buf[n:], p)
	if mask {
		for i := 0; i < l; i++ {
			buf[n+i] ^= key[i&3]
		}
	}
	_, err := w.Write(buf)
	return err
}

// WriteFrame — FIN 이 켜진 프레임 하나. 테스트에서 "클라이언트인 척" 할 때도 쓴다.
func WriteFrame(w io.Writer, op byte, p []byte, mask bool) error {
	return writeRaw(w, true, op, p, mask)
}

// 서버가 내보내는 프레임은 절대 마스킹하지 않는다 (RFC 6455 §5.1).
func (c *Conn) write(op byte, p []byte) error {
	c.wmu.Lock()
	defer c.wmu.Unlock()
	if c.closed {
		return net.ErrClosed
	}
	return writeRaw(c.c, true, op, p, c.Client)
}
func (c *Conn) WriteText(p []byte) error { return c.write(OpText, p) }
func (c *Conn) Close() error {
	c.wmu.Lock()
	c.closed = true
	c.wmu.Unlock()
	return c.c.Close()
}

// ── 프레임 읽기 ──
func (c *Conn) readFrame() (fin bool, op byte, payload []byte, err error) {
	var h [2]byte
	if _, err = io.ReadFull(c.br, h[:]); err != nil {
		return
	}
	fin = h[0]&0x80 != 0
	if h[0]&0x70 != 0 {
		err = errors.New("RSV 비트가 켜져 있다 (확장을 협상한 적이 없다)")
		return
	}
	op = h[0] & 0x0f
	masked := h[1]&0x80 != 0
	if !masked && !c.Client {
		// 클라이언트→서버 프레임은 반드시 마스킹돼야 한다. 이건 보안이 아니라
		// 중간의 낡은 캐시 프록시가 본문을 HTTP 로 오해하지 못하게 하는 장치다.
		err = errors.New("마스킹되지 않은 클라이언트 프레임")
		return
	}
	if masked && c.Client {
		err = errors.New("서버가 마스킹된 프레임을 보냈다")
		return
	}
	l := int64(h[1] & 0x7f)
	switch l {
	case 126:
		var e [2]byte
		if _, err = io.ReadFull(c.br, e[:]); err != nil {
			return
		}
		l = int64(binary.BigEndian.Uint16(e[:]))
	case 127:
		var e [8]byte
		if _, err = io.ReadFull(c.br, e[:]); err != nil {
			return
		}
		u := binary.BigEndian.Uint64(e[:])
		if u > 1<<62 {
			err = errors.New("길이가 말이 안 된다")
			return
		}
		l = int64(u)
	}
	if l > c.MaxPayload {
		err = fmt.Errorf("프레임이 상한을 넘었다 (%d > %d)", l, c.MaxPayload)
		return
	}
	var key [4]byte
	if masked {
		if _, err = io.ReadFull(c.br, key[:]); err != nil {
			return
		}
	}
	payload = make([]byte, l)
	if _, err = io.ReadFull(c.br, payload); err != nil {
		return
	}
	if masked {
		for i := range payload { // 마스크 해제 = 4바이트 키로 XOR
			payload[i] ^= key[i&3]
		}
	}
	return
}

// ReadMessage — 조각난 프레임을 이어 붙여 메시지 하나를 돌려준다.
// 제어 프레임(핑/퐁/닫기)은 여기서 삼키고 애플리케이션에 올리지 않는다.
func (c *Conn) ReadMessage() (byte, []byte, error) {
	var msgOp byte
	var buf []byte
	for {
		fin, op, p, err := c.readFrame()
		if err != nil {
			return 0, nil, err
		}
		if op&0x8 != 0 { // 제어 프레임
			if !fin || len(p) > 125 {
				return 0, nil, errors.New("제어 프레임은 조각날 수 없고 125바이트를 넘을 수 없다")
			}
			switch op {
			case OpPing:
				if err := c.write(OpPong, p); err != nil {
					return 0, nil, err
				}
			case OpClose:
				// 닫기는 인사를 돌려주고 끝낸다. 상대가 이미 사라졌을 수 있으니
				// 여기서 영원히 매달리지 않도록 짧은 마감을 건다.
				c.c.SetWriteDeadline(time.Now().Add(500 * time.Millisecond))
				c.write(OpClose, p)
				c.c.SetWriteDeadline(time.Time{})
				return 0, nil, io.EOF
			case OpPong: // 살아 있다는 신호. 할 일 없음
			}
			continue
		}
		if op == OpCont {
			if msgOp == 0 {
				return 0, nil, errors.New("이어 붙일 메시지가 없다")
			}
			buf = append(buf, p...)
		} else {
			if msgOp != 0 {
				return 0, nil, errors.New("앞 메시지가 끝나지 않았다")
			}
			msgOp = op
			buf = p
		}
		if int64(len(buf)) > c.MaxPayload {
			return 0, nil, errors.New("조각 합계가 상한을 넘었다")
		}
		if fin {
			return msgOp, buf, nil
		}
	}
}

// ── 클라이언트 쪽 ──
// 서버만 있으면 테스트를 못 쓴다. Dial 은 40줄이면 되고, 운영 도구로도 쓸모가 있다.
// Client 가 켜지면 방향이 뒤집힌다 — 보낼 때 마스킹하고, 받을 때 마스킹을 요구하지 않는다.
func Dial(rawurl string) (*Conn, error) {
	u, err := url.Parse(rawurl)
	if err != nil {
		return nil, err
	}
	host := u.Host
	if !strings.Contains(host, ":") {
		host += ":80"
	}
	c, err := net.Dial("tcp", host)
	if err != nil {
		return nil, err
	}
	var nonce [16]byte
	if _, err := rand.Read(nonce[:]); err != nil {
		c.Close()
		return nil, err
	}
	key := base64.StdEncoding.EncodeToString(nonce[:])
	path := u.RequestURI()
	if path == "" {
		path = "/"
	}
	req := fmt.Sprintf("GET %s HTTP/1.1\r\nHost: %s\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"+
		"Sec-WebSocket-Key: %s\r\nSec-WebSocket-Version: 13\r\n\r\n", path, u.Host, key)
	if _, err := io.WriteString(c, req); err != nil {
		c.Close()
		return nil, err
	}
	br := bufio.NewReader(c)
	resp, err := http.ReadResponse(br, nil)
	if err != nil {
		c.Close()
		return nil, err
	}
	resp.Body.Close()
	if resp.StatusCode != 101 {
		c.Close()
		return nil, fmt.Errorf("업그레이드 거절: %s", resp.Status)
	}
	if got := resp.Header.Get("Sec-WebSocket-Accept"); got != AcceptKey(key) {
		c.Close()
		return nil, errors.New("Sec-WebSocket-Accept 가 맞지 않는다")
	}
	conn := newConn(c, br)
	conn.Client = true
	return conn, nil
}
