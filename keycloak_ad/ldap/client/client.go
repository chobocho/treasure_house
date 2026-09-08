// client — LDAP 서버에 물어보는 쪽.
//
// 3부에서 만든 것을 라이브러리로 뽑았다. 두 곳이 이것을 쓴다.
//
//	ldapcli   사람이 바이트를 눈으로 보려고 (3부)
//	miniidp   우리가 만든 인증 서버가 AD 에 물어보려고 (4부)
//
// 두 번째가 이 덱의 요점이다. Keycloak 이 하는 일의 절반은
// "앱에게는 OIDC 로 답하고, 뒤에서는 LDAP 으로 묻는" 통역이고,
// 그 LDAP 쪽이 정확히 이 파일이다.
//
// Trace 를 걸면 오간 바이트를 그대로 넘겨받는다 — ldapcli 가 그것을
// 풀어 보여 준다. 라이브러리가 화면에 찍지 않고 갈고리만 내주는 이유는,
// 서버 안에서 도는 miniidp 는 그런 출력을 원하지 않기 때문이다.
package client

import (
	"crypto/tls"
	"crypto/x509"
	"errors"
	"fmt"
	"net"
	"os"
	"strings"
	"time"

	"treasure/keycloak_ad/ldap/ber"
	"treasure/keycloak_ad/ldap/proto"
)

// Options 는 어떻게 붙을 것인가.
type Options struct {
	TLS        bool          // 참이면 처음부터 TLS (LDAPS, 636)
	CAFile     string        // 믿을 CA 인증서 파일
	ServerName string        // 인증서에서 확인할 이름
	Insecure   bool          // 인증서를 확인하지 않는다 (위험)
	Timeout    time.Duration // 붙기와 읽기의 기한
}

// Conn 은 열린 연결 하나다. LDAP 은 연결마다 신분을 기억하므로,
// 이 값 하나가 곧 "지금 누구로 붙어 있는가" 이기도 하다(3부 5장).
type Conn struct {
	c    net.Conn
	buf  []byte
	seq  int64
	opts Options

	// Trace 는 오간 바이트를 그대로 넘겨준다. dir 은 "→" 또는 "←".
	Trace func(dir string, raw []byte)
}

// Entry 는 찾은 항목 하나다. 속성 이름은 소문자로 통일해 담는다 —
// LDAP 은 이름의 대소문자를 가리지 않기 때문이다.
type Entry struct {
	DN    string
	Attrs map[string][][]byte
}

// First 는 속성의 첫 값을 글자로. 없으면 빈 글자.
func (e Entry) First(name string) string {
	v := e.Attrs[strings.ToLower(name)]
	if len(v) == 0 {
		return ""
	}
	return string(v[0])
}

// Values 는 속성의 값 전부를 글자로. memberOf 처럼 여럿인 칸에 쓴다.
func (e Entry) Values(name string) []string {
	var out []string
	for _, v := range e.Attrs[strings.ToLower(name)] {
		out = append(out, string(v))
	}
	return out
}

// BindError 는 바인드가 거절당했을 때의 오류다.
//
// 결과 코드만이 아니라 **진단 문구를 통째로** 들고 다니는 것이
// 중요하다. AD 는 실패 이유를 그 문구 끝의 "data XXX" 로만 알려 주기
// 때문이다(3부 5장).
type BindError struct {
	Code int
	Diag string
}

// Error 는 진단 문구까지 통째로 담는다.
//
// 한 줄이 140칸을 넘어 화면에서는 읽기 어렵지만, 그렇다고 여기서 잘라
// 내면 오류를 그냥 로그로 흘려보내는 쪽에서 **진짜 이유를 잃는다**.
// 폭 문제는 보여 주는 쪽에서 접어 푼다(ldapcli 의 explainBind).
func (e *BindError) Error() string {
	if e.Diag == "" {
		return fmt.Sprintf("바인드 실패: %s", proto.ResultName(e.Code))
	}
	return fmt.Sprintf("바인드 실패: %s — %s",
		proto.ResultName(e.Code), e.Diag)
}

// ADCode 는 진단 문구에서 "data XXX" 의 XXX 를 뽑는다. 없으면 빈 글자.
func (e *BindError) ADCode() string {
	i := strings.Index(e.Diag, "data ")
	if i < 0 {
		return ""
	}
	rest := e.Diag[i+len("data "):]
	end := strings.IndexAny(rest, ", ")
	if end < 0 {
		end = len(rest)
	}
	return strings.TrimSpace(rest[:end])
}

// Dial 은 연결을 연다. 아직 아무도 아닌 상태다 — Bind 를 해야 한다.
func Dial(addr string, o Options) (*Conn, error) {
	if o.Timeout == 0 {
		o.Timeout = 10 * time.Second
	}
	if !o.TLS {
		c, err := net.DialTimeout("tcp", addr, o.Timeout)
		if err != nil {
			return nil, err
		}
		return &Conn{c: c, opts: o}, nil
	}

	cfg := &tls.Config{InsecureSkipVerify: o.Insecure}
	if o.ServerName != "" {
		cfg.ServerName = o.ServerName
	}
	if o.CAFile != "" {
		pem, err := os.ReadFile(o.CAFile)
		if err != nil {
			return nil, err
		}
		pool := x509.NewCertPool()
		if !pool.AppendCertsFromPEM(pem) {
			return nil, fmt.Errorf("%s 를 CA 로 못 읽겠다", o.CAFile)
		}
		cfg.RootCAs = pool
	}
	d := &net.Dialer{Timeout: o.Timeout}
	c, err := tls.DialWithDialer(d, "tcp", addr, cfg)
	if err != nil {
		return nil, err
	}
	return &Conn{c: c, opts: o}, nil
}

func (c *Conn) Close() error { return c.c.Close() }

func (c *Conn) next() int64 { c.seq++; return c.seq }

func (c *Conn) trace(dir string, raw []byte) {
	if c.Trace != nil {
		c.Trace(dir, raw)
	}
}

func (c *Conn) send(raw []byte) error {
	c.trace("→", raw)
	_, err := c.c.Write(raw)
	return err
}

// recv 는 답 한 통을 받는다.
//
// 3부 4장의 MessageLength 가 여기서 일한다 — 지금 가진 바이트로 한 통이
// 완성되는지, 아니면 더 읽어야 하는지를 그 함수가 알려 준다.
func (c *Conn) recv() (proto.Message, error) {
	c.c.SetReadDeadline(time.Now().Add(c.opts.Timeout))
	tmp := make([]byte, 4096)
	for {
		n, err := ber.MessageLength(c.buf)
		if err == nil && len(c.buf) >= n {
			raw := c.buf[:n]
			c.buf = c.buf[n:]
			c.trace("←", raw)
			return proto.ParseMessage(raw)
		}
		if err != nil && err != ber.ErrShort {
			return proto.Message{}, err
		}
		r, rerr := c.c.Read(tmp)
		if r > 0 {
			c.buf = append(c.buf, tmp[:r]...)
			continue
		}
		return proto.Message{}, fmt.Errorf("더 읽을 수 없다: %v", rerr)
	}
}

func cat(parts ...[]byte) []byte {
	var out []byte
	for _, p := range parts {
		out = append(out, p...)
	}
	return out
}

// Bind 는 "나는 이 사람이다" 를 선언한다.
//
// 성공하면 이 연결의 신분이 그 DN 이 되고, 실패하면 아무도 아닌 상태로
// 돌아간다(3부 5장). 그래서 miniidp 는 사용자 확인용 연결을 따로 연다.
func (c *Conn) Bind(dn, password string) error {
	id := c.next()
	raw := ber.Seq(ber.Int(id),
		ber.Encode(ber.Tag(ber.Application, true, proto.OpBindRequest),
			cat(ber.Int(3), ber.Str(dn),
				ber.Encode(ber.Tag(ber.Context, false, 0),
					[]byte(password)))))
	if err := c.send(raw); err != nil {
		return err
	}
	msg, err := c.recv()
	if err != nil {
		return err
	}
	if msg.OpNum() != proto.OpBindResponse {
		return fmt.Errorf("바인드에 [%d] 로 답했다", msg.OpNum())
	}
	kids, err := ber.Children(msg.Op.Value)
	if err != nil || len(kids) < 3 {
		return errors.New("바인드 응답을 못 읽는다")
	}
	code, _ := kids[0].Int()
	if int(code) != proto.ResultSuccess {
		return &BindError{Code: int(code), Diag: kids[2].Str()}
	}
	return nil
}

// Search 는 조건에 맞는 항목을 모아 온다.
//
// 답은 "찾은 것 여러 통 + 끝났다는 통 하나" 로 오므로(3부 6장),
// Done 이 올 때까지 읽는다.
func (c *Conn) Search(base string, scope int, filter string,
	attrs []string) ([]Entry, error) {
	f, err := proto.ParseFilterString(filter)
	if err != nil {
		return nil, fmt.Errorf("필터: %w", err)
	}
	var al [][]byte
	for _, a := range attrs {
		al = append(al, ber.Str(a))
	}
	id := c.next()
	raw := ber.Seq(ber.Int(id),
		ber.Encode(
			ber.Tag(ber.Application, true, proto.OpSearchRequest),
			cat(ber.Str(base), ber.Enum(int64(scope)), ber.Enum(0),
				ber.Int(0), ber.Int(0), ber.Bool(false),
				proto.EncodeFilter(f), ber.Seq(al...))))
	if err := c.send(raw); err != nil {
		return nil, err
	}

	var out []Entry
	for {
		msg, err := c.recv()
		if err != nil {
			return nil, err
		}
		switch msg.OpNum() {
		case proto.OpSearchResultEntry:
			e, err := parseEntry(msg)
			if err != nil {
				return nil, err
			}
			out = append(out, e)
		case proto.OpSearchResultDone:
			kids, err := ber.Children(msg.Op.Value)
			if err != nil || len(kids) < 3 {
				return nil, errors.New("Done 을 못 읽는다")
			}
			code, _ := kids[0].Int()
			if int(code) != proto.ResultSuccess {
				return nil, fmt.Errorf("검색 실패: %s — %s",
					proto.ResultName(int(code)), kids[2].Str())
			}
			return out, nil
		default:
			// SearchResultReference 따위. 이 덱에서는 나올 일이 없다.
			continue
		}
	}
}

func parseEntry(msg proto.Message) (Entry, error) {
	kids, err := ber.Children(msg.Op.Value)
	if err != nil || len(kids) < 2 {
		return Entry{}, errors.New("항목을 못 읽는다")
	}
	e := Entry{DN: kids[0].Str(), Attrs: map[string][][]byte{}}
	attrs, err := ber.Children(kids[1].Value)
	if err != nil {
		return Entry{}, err
	}
	for _, a := range attrs {
		one, err := ber.Children(a.Value)
		if err != nil || len(one) < 2 {
			continue
		}
		vals, err := ber.Children(one[1].Value)
		if err != nil {
			continue
		}
		name := strings.ToLower(one[0].Str())
		for _, v := range vals {
			e.Attrs[name] = append(e.Attrs[name], v.Value)
		}
	}
	return e, nil
}
