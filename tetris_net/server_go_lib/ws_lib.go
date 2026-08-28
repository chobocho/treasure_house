package main

// ws_lib.go — gorilla/websocket 을 ws.go 와 똑같은 겉모양으로 감싼다.
//
// 이 디렉터리의 room.go·hub.go·main.go·테스트 2종은 server_go 에서 Makefile 이
// byte-for-byte 복사해 온 것이다 (make lib-copy). 검증받은 파일과 여기서 도는
// 파일이 갈리면 안 된다 — make web 이 room.mjs 를 다루는 규칙과 같다.
// 그러니 이 파일이 증명하는 건 하나다: 직접 구현 ws.go 339줄을 라이브러리로
// 갈아 끼우면 이만큼이 남고, 나머지 층은 전송이 뭔지 모른 채 그대로 돈다.
//
// 직접 구현과 견주면: 핸드셰이크·프레임 코덱·마스킹·close 협상이 전부
// 라이브러리 속으로 사라졌다. 대신 의존성 0 이 깨진다 — go.sum 이 생긴다.

import (
	"net/http"
	"time"

	"github.com/gorilla/websocket"
)

// 프레임 종류 — hub.go 가 OpText 를 참조한다. gorilla 의 메시지 상수(TextMessage=1 등)는
// RFC 6455 오프코드 값을 그대로 쓰므로 byte 로 캐스팅하면 이 표와 정확히 일치한다.
const (
	OpCont   byte = 0x0
	OpText   byte = 0x1
	OpBinary byte = 0x2
	OpClose  byte = 0x8
	OpPing   byte = 0x9
	OpPong   byte = 0xA
)

// Conn — ws.go 의 Conn 과 같은 겉모양. 속만 *websocket.Conn 으로 바뀌었다.
type Conn struct {
	ws         *websocket.Conn
	MaxPayload int64 // 한 메시지의 상한. hub 가 Upgrade 뒤에 바꿔 끼우므로 필드로 남겨 둔다
	Client     bool  // 마스킹 방향은 라이브러리가 알아서 한다 — 겉모양 유지용
}

var upgrader = websocket.Upgrader{
	ReadBufferSize:  4096,
	WriteBufferSize: 4096,
	// 직접 구현 ws.go 도 Origin 을 검사하지 않았다. 같은 규칙을 유지한다 —
	// 이 서버는 방 코드를 아는 사람만 의미 있는 일을 할 수 있다.
	CheckOrigin: func(*http.Request) bool { return true },
}

// Upgrade — ws.go 의 70~155줄(핸드셰이크 86줄)이 이 세 줄로 줄어든다.
func Upgrade(w http.ResponseWriter, r *http.Request) (*Conn, error) {
	c, err := upgrader.Upgrade(w, r, nil)
	if err != nil {
		return nil, err
	}
	return &Conn{ws: c, MaxPayload: 1 << 20}, nil
}

// Dial — 클라이언트 쪽. 테스트(hub_test.go)가 쓴다.
func Dial(url string) (*Conn, error) {
	c, _, err := websocket.DefaultDialer.Dial(url, nil)
	if err != nil {
		return nil, err
	}
	return &Conn{ws: c, MaxPayload: 1 << 20, Client: true}, nil
}

// ReadMessage — 조각 조립·제어 프레임 응답은 라이브러리 몫이다.
// 여기 도착하는 건 텍스트/바이너리 메시지뿐이라 오프코드 변환이 곧 항등이다.
func (c *Conn) ReadMessage() (byte, []byte, error) {
	// MaxPayload 는 Upgrade 뒤에 바뀔 수 있으므로 읽기 직전에 반영한다
	c.ws.SetReadLimit(c.MaxPayload)
	mt, data, err := c.ws.ReadMessage()
	if err != nil {
		return 0, nil, err
	}
	return byte(mt), data, nil
}

func (c *Conn) WriteText(p []byte) error {
	return c.ws.WriteMessage(websocket.TextMessage, p)
}

// Close — 성의 표시로 close 프레임을 먼저 보낸다. 실패해도 소켓은 닫는다.
// WriteControl 은 다른 쓰기와 동시에 불러도 안전하다고 gorilla 가 보증한다.
func (c *Conn) Close() error {
	c.ws.WriteControl(websocket.CloseMessage,
		websocket.FormatCloseMessage(websocket.CloseNormalClosure, ""),
		time.Now().Add(time.Second))
	return c.ws.Close()
}
