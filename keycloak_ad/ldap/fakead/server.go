// server.go — 가짜 AD 의 문지기.
//
// 하는 일은 단순하다. 손님이 붙으면 그 손님만 보는 goroutine 하나를
// 띄우고, 그 안에서 "한 통 읽기 → 처리 → 답 쓰기" 를 연결이 끊길 때까지
// 되풀이한다.
//
// 우리가 흉내 내는 것 (Keycloak 이 실제로 쓰는 것)
//
//	· simple bind (서비스 계정 DN, 사용자 DN·UPN)
//	· search — base/one/sub 범위, 필터, 속성 고르기
//	· Simple Paged Results 컨트롤 (RFC 2696) — 받아서 한 쪽으로 답한다
//	· unbind
//	· 636 쪽의 LDAPS
//
// 일부러 안 하는 것 (3부에서 슬라이드 한 장으로 밝힌다)
//
//	· StartTLS — 389 로 붙은 뒤 도중에 암호화로 바꾸는 방식
//	· SASL / GSSAPI / Kerberos — 3부에서 개념만 다룬다
//	· modify / add / delete — 우리 연동은 읽기 전용이다
//	· referral(다른 서버로 넘기기), 글로벌 카탈로그 3268
//
// 안 하는 것을 "조용히 무시" 하지 않고 unwillingToPerform(53)으로
// 분명히 거절하는 것이 중요하다. 무시하면 상대는 우리가 한 줄로 안다.
package fakead

import (
	"crypto/tls"
	"fmt"
	"io"
	"net"
	"strings"
	"sync"
	"time"

	"treasure/keycloak_ad/ldap/ber"
	"treasure/keycloak_ad/ldap/proto"
)

// 한 통의 최대 크기. 이보다 큰 길이를 적어 보내면 끊는다 —
// 안 그러면 "길이 2GB" 한 줄로 서버의 메모리를 말릴 수 있다.
const maxMessage = 1 << 20

type Server struct {
	dir *Dir
	log io.Writer

	mu      sync.Mutex
	plain   net.Listener
	tlsLn   net.Listener
	closed  bool
	connSeq int64
	// 살아 있는 연결들. 끌 때 이것들을 함께 닫아야 한다 — 손님이 조용히
	// 붙어만 있으면 읽기에서 5분을 기다리느라 서버가 안 꺼진다.
	live  map[net.Conn]bool
	logMu sync.Mutex
	nowFn func() time.Time
	wg    sync.WaitGroup
}

func NewServer(d *Dir, logw io.Writer) *Server {
	s := &Server{dir: d, log: logw, nowFn: time.Now,
		live: map[net.Conn]bool{}}
	// 날짜는 파일 머리에 한 번만 적는다. 줄마다 적으면 20칸을 늘
	// 쓰는데, 긴 DN 이 들어오는 줄이 화면 밖으로 밀린다.
	s.logf("가짜 AD 시작 — %s", s.nowFn().Format("2006-01-02"))
	return s
}

func (s *Server) Addr() string {
	if s.plain == nil {
		return ""
	}
	return s.plain.Addr().String()
}

func (s *Server) TLSAddr() string {
	if s.tlsLn == nil {
		return ""
	}
	return s.tlsLn.Addr().String()
}

func (s *Server) ListenPlain(addr string) error {
	ln, err := net.Listen("tcp", addr)
	if err != nil {
		return err
	}
	s.plain = ln
	s.wg.Add(1)
	go s.accept(ln, "평문")
	return nil
}

func (s *Server) ListenTLS(addr, certFile, keyFile string) error {
	cert, err := tls.LoadX509KeyPair(certFile, keyFile)
	if err != nil {
		return fmt.Errorf("인증서: %w", err)
	}
	ln, err := tls.Listen("tcp", addr, &tls.Config{
		Certificates: []tls.Certificate{cert},
		MinVersion:   tls.VersionTLS12,
	})
	if err != nil {
		return err
	}
	s.tlsLn = ln
	s.wg.Add(1)
	go s.accept(ln, "LDAPS")
	return nil
}

func (s *Server) Close() {
	s.mu.Lock()
	s.closed = true
	s.mu.Unlock()
	if s.plain != nil {
		s.plain.Close()
	}
	if s.tlsLn != nil {
		s.tlsLn.Close()
	}
	// 붙어 있는 손님도 끊는다. 안 그러면 읽기 기한(5분)이 지날 때까지
	// 여기서 기다린다.
	s.mu.Lock()
	for c := range s.live {
		c.Close()
	}
	s.mu.Unlock()
	s.wg.Wait()
}

func (s *Server) isClosed() bool {
	s.mu.Lock()
	defer s.mu.Unlock()
	return s.closed
}

func (s *Server) accept(ln net.Listener, kind string) {
	defer s.wg.Done()
	for {
		c, err := ln.Accept()
		if err != nil {
			if s.isClosed() {
				return
			}
			continue
		}
		s.mu.Lock()
		s.connSeq++
		id := s.connSeq
		s.mu.Unlock()
		s.wg.Add(1)
		go func() {
			defer s.wg.Done()
			s.serve(c, id, kind)
		}()
	}
}

// logf 는 오간 것을 사람이 읽는 한 줄로 남긴다.
//
// 이 로그가 이 프로그램에서 가장 값진 산출물이다. 7부에서 "Keycloak 이
// AD 에게 대체 무엇을 물었나" 를 알아내는 방법이 바로 이 파일을 읽는
// 것이다. 그래서 필터를 바이트가 아니라 사람이 읽는 글(RFC 4515)로
// 되돌려 적는다.
func (s *Server) logf(format string, args ...any) {
	if s.log == nil {
		return
	}
	s.logMu.Lock()
	defer s.logMu.Unlock()
	fmt.Fprintf(s.log, "%s %s\n",
		s.nowFn().Format("15:04:05"),
		fmt.Sprintf(format, args...))
}

// session 은 연결 하나가 들고 있는 상태다. LDAP 은 연결 단위로
// "지금 누구인가" 를 기억한다 — HTTP 와 가장 다른 점이다.
type session struct {
	id    int64
	bound string // 바인드된 DN. 비어 있으면 아직 아무도 아니다
}

func (s *Server) serve(c net.Conn, id int64, kind string) {
	s.mu.Lock()
	s.live[c] = true
	s.mu.Unlock()
	defer func() {
		s.mu.Lock()
		delete(s.live, c)
		s.mu.Unlock()
		c.Close()
	}()
	sess := &session{id: id}
	s.logf("[%d] %s 연결됨 (%s)", id, c.RemoteAddr(), kind)
	defer s.logf("[%d] 끊김", id)

	var buf []byte
	tmp := make([]byte, 4096)
	for {
		// 한 통이 다 왔는지 본다. 덜 왔으면 더 읽는다.
		n, err := ber.MessageLength(buf)
		if err == ber.ErrShort || (err == nil && len(buf) < n) {
			c.SetReadDeadline(time.Now().Add(5 * time.Minute))
			r, rerr := c.Read(tmp)
			if r > 0 {
				buf = append(buf, tmp[:r]...)
				continue
			}
			if rerr != nil {
				return
			}
			continue
		}
		if err != nil {
			s.logf("[%d] 못 읽을 바이트 — 끊는다: %v", id, err)
			return
		}
		if n > maxMessage {
			s.logf("[%d] 한 통이 %d바이트 — 너무 크다. 끊는다", id, n)
			return
		}
		raw := buf[:n]
		buf = buf[n:]

		reply, keep := s.handle(sess, raw)
		if len(reply) > 0 {
			if _, werr := c.Write(reply); werr != nil {
				return
			}
		}
		if !keep {
			return
		}
	}
}

// handle 은 한 통을 처리하고 (답, 연결을 이어 갈지) 를 돌려준다.
func (s *Server) handle(sess *session, raw []byte) ([]byte, bool) {
	msg, err := proto.ParseMessage(raw)
	if err != nil {
		s.logf("[%d] 메시지를 못 읽는다 — 끊는다: %v", sess.id, err)
		return nil, false
	}

	switch msg.OpNum() {
	case proto.OpBindRequest:
		return s.handleBind(sess, msg), true
	case proto.OpUnbindRequest:
		// unbind 에는 답이 없다. 규약이 그렇다 — 그냥 끊는다.
		s.logf("[%d] #%d UNBIND", sess.id, msg.ID)
		return nil, false
	case proto.OpSearchRequest:
		return s.handleSearch(sess, msg), true
	}

	s.logf("[%d] #%d 지원하지 않는 연산 [%d]",
		sess.id, msg.ID, msg.OpNum())
	return proto.SearchResultDone(msg.ID,
		proto.ResultUnwillingToPerform, "",
		"이 서버는 읽기만 한다 (bind·search·unbind)"), true
}

func (s *Server) handleBind(sess *session, msg proto.Message) []byte {
	br, err := proto.ParseBindRequest(msg.Op)
	if err != nil {
		// SASL 로 온 것이다. 못 한다고 분명히 말한다.
		sess.bound = ""
		s.logf("[%d] #%d BIND — %v", sess.id, msg.ID, err)
		return proto.BindResponse(msg.ID,
			proto.ResultAuthMethodNotSupported, "",
			"simple 인증만 지원한다 (SASL·GSSAPI 없음)")
	}
	if br.Version != 3 {
		sess.bound = ""
		return proto.BindResponse(msg.ID, proto.ResultProtocolError, "",
			fmt.Sprintf("LDAP v%d — 이 서버는 v3 만 한다", br.Version))
	}

	code, diag := s.dir.Bind(br.Name, br.Password)
	if code == proto.ResultSuccess {
		sess.bound = br.Name
	} else {
		// 실패한 바인드는 그 연결의 신분을 지운다(RFC 4511 §4.2.1).
		// 안 지우면 "한 번 성공한 뒤 실패해도 계속 그 사람" 이 된다.
		sess.bound = ""
	}
	s.logf("[%d] #%d BIND dn=%q → %s", sess.id, msg.ID, br.Name,
		proto.ResultName(code))
	return proto.BindResponse(msg.ID, code, "", diag)
}

func (s *Server) handleSearch(sess *session, msg proto.Message) []byte {
	sr, err := proto.ParseSearchRequest(msg.Op)
	if err != nil {
		s.logf("[%d] #%d SEARCH — 읽을 수 없다: %v",
			sess.id, msg.ID, err)
		return proto.SearchResultDone(msg.ID,
			proto.ResultProtocolError, "", err.Error())
	}

	// 모르는 컨트롤에 criticality=TRUE 가 붙어 있으면 거절해야 한다.
	// "못 하겠으면 아예 하지 마라" 는 뜻이기 때문이다 (RFC 4511
	// §4.1.11).
	var paged *proto.PagedResults
	for _, c := range msg.Controls {
		if c.OID == proto.OIDPagedResults {
			p, perr := proto.ParsePagedResults(c.Value)
			if perr == nil {
				paged = &p
			}
			continue
		}
		if c.Critical {
			s.logf("[%d] #%d SEARCH — 모르는 필수 컨트롤 %s",
				sess.id, msg.ID, c.OID)
			return proto.SearchResultDone(msg.ID,
				proto.ResultUnavailableCriticalExtension, "", c.OID)
		}
	}

	// 익명 검색은 막는다. 진짜 AD 의 기본이 그렇고, 그래서 Keycloak 에
	// 서비스 계정을 적어 줘야 한다 (7부).
	if sess.bound == "" {
		s.logf("[%d] #%d SEARCH base=%q — 바인드 전이라 거절",
			sess.id, msg.ID, sr.BaseDN)
		return proto.SearchResultDone(msg.ID,
			proto.ResultInsufficientAccessRights, "",
			"먼저 바인드해야 한다 (익명 검색 불가)")
	}

	if s.dir.Get(sr.BaseDN) == nil {
		s.logf("[%d] #%d SEARCH base=%q → noSuchObject",
			sess.id, msg.ID, sr.BaseDN)
		return proto.SearchResultDone(msg.ID,
			proto.ResultNoSuchObject, "", "그런 base 가 없다")
	}

	found := s.dir.Search(sr.BaseDN, sr.Scope, sr.Filter)
	var out []byte
	code := proto.ResultSuccess
	sent := 0
	for _, e := range found {
		if sr.SizeLimit > 0 && int64(sent) >= sr.SizeLimit {
			code = proto.ResultSizeLimitExceeded
			break
		}
		out = append(out, proto.SearchResultEntry(msg.ID, e.DN,
			s.dir.Attributes(e, sr.Attrs))...)
		sent++
	}

	var controls [][]byte
	if paged != nil {
		// 우리 자료는 열댓 건이라 한 쪽에 다 담긴다. 빈 쿠키는
		// "다음 쪽은 없다" 는 뜻이고, Keycloak 은 그걸 보고 멈춘다.
		done := proto.PagedResults{Size: int64(sent)}
		controls = append(controls, proto.EncodeControl(
			proto.OIDPagedResults, false, done.Encode()))
	}

	// 검색 한 건을 세 줄로 나눠 적는다. 한 줄에 몰면 140칸이 넘어
	// 좁은 화면에서 정작 봐야 할 필터가 오른쪽으로 밀려 안 보인다.
	s.logf("[%d] #%d SEARCH base=%q scope=%s",
		sess.id, msg.ID, sr.BaseDN, proto.ScopeName(sr.Scope))
	s.logf("[%d] #%d        filter=%s", sess.id, msg.ID,
		sr.Filter.String())
	s.logf("[%d] #%d        attrs=%s → %d건 %s", sess.id, msg.ID,
		attrList(sr.Attrs), sent, proto.ResultName(code))

	return append(out, proto.SearchResultDone(msg.ID, code, "", "",
		controls...)...)
}

func attrList(a []string) string {
	if len(a) == 0 {
		return "[전부]"
	}
	return "[" + strings.Join(a, " ") + "]"
}
