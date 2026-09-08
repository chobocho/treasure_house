package fakead

import (
	"bytes"
	"crypto/tls"
	"crypto/x509"
	"io"
	"net"
	"os"
	"strings"
	"testing"
	"time"

	"treasure/keycloak_ad/ldap/ber"
	"treasure/keycloak_ad/ldap/proto"
)

// conn 은 시험용 손님이다. 진짜 소켓으로 진짜 바이트를 주고받는다 —
// 서버가 TCP 위에서 제대로 도는지는 이렇게만 확인할 수 있다.
type conn struct {
	t   *testing.T
	c   net.Conn
	buf []byte
	id  int64
}

func dial(t *testing.T, srv *Server) *conn {
	t.Helper()
	c, err := net.Dial("tcp", srv.Addr())
	if err != nil {
		t.Fatalf("붙지 못했다: %v", err)
	}
	t.Cleanup(func() { c.Close() })
	return &conn{t: t, c: c}
}

func (k *conn) send(makeOp func(id int64) []byte) int64 {
	k.t.Helper()
	k.id++
	if _, err := k.c.Write(makeOp(k.id)); err != nil {
		k.t.Fatalf("보내지 못했다: %v", err)
	}
	return k.id
}

// recv 는 응답 한 통을 받는다. 여러 통이 한 번에 붙어 와도 하나씩 떼어
// 낸다.
func (k *conn) recv() proto.Message {
	k.t.Helper()
	k.c.SetReadDeadline(time.Now().Add(3 * time.Second))
	for {
		if n, err := ber.MessageLength(k.buf); err == nil && len(k.buf) >= n {
			msg, err := proto.ParseMessage(k.buf[:n])
			if err != nil {
				k.t.Fatalf("응답을 못 읽는다: %v", err)
			}
			k.buf = k.buf[n:]
			return msg
		}
		tmp := make([]byte, 4096)
		n, err := k.c.Read(tmp)
		if n > 0 {
			k.buf = append(k.buf, tmp[:n]...)
			continue
		}
		k.t.Fatalf("더 읽을 수 없다: %v", err)
	}
}

func bindOp(dn, pass string) func(int64) []byte {
	return func(id int64) []byte {
		return ber.Seq(ber.Int(id),
			ber.Encode(ber.Tag(ber.Application, true, proto.OpBindRequest),
				concat(ber.Int(3), ber.Str(dn),
					ber.Encode(ber.Tag(ber.Context, false, 0),
						[]byte(pass)))))
	}
}

func searchOp(base string, scope int, filter string, attrs []string,
	controls []byte) func(int64) []byte {
	return func(id int64) []byte {
		f, err := proto.ParseFilterString(filter)
		if err != nil {
			panic(err)
		}
		var al [][]byte
		for _, a := range attrs {
			al = append(al, ber.Str(a))
		}
		parts := []([]byte){
			ber.Int(id),
			ber.Encode(ber.Tag(ber.Application, true, proto.OpSearchRequest),
				concat(ber.Str(base), ber.Enum(int64(scope)), ber.Enum(0),
					ber.Int(0), ber.Int(0), ber.Bool(false),
					proto.EncodeFilter(f), ber.Seq(al...))),
		}
		if controls != nil {
			parts = append(parts,
				ber.Encode(ber.Tag(ber.Context, true, 0), controls))
		}
		return ber.Seq(parts...)
	}
}

func concat(parts ...[]byte) []byte {
	var out []byte
	for _, p := range parts {
		out = append(out, p...)
	}
	return out
}

func start(t *testing.T) *Server {
	t.Helper()
	d, err := LoadLDIFFile("../../data/campus.ldif")
	if err != nil {
		t.Fatal(err)
	}
	srv := NewServer(d, io.Discard)
	if err := srv.ListenPlain("127.0.0.1:0"); err != nil {
		t.Fatal(err)
	}
	t.Cleanup(srv.Close)
	return srv
}

// ── 바인드 ───────────────────────────────────────────────────────────

func TestServerBindSuccess(t *testing.T) {
	srv := start(t)
	k := dial(t, srv)
	id := k.send(bindOp("CN=Kim Minji,OU=Students,"+base, "Passw0rd!-demo"))
	res := k.recv()
	if res.ID != id {
		t.Errorf("messageID = %d, 물어본 것 %d", res.ID, id)
	}
	if res.OpNum() != proto.OpBindResponse {
		t.Fatalf("연산 = %d", res.OpNum())
	}
	code, diag := resultOf(t, res)
	if code != proto.ResultSuccess {
		t.Errorf("코드 %d · %s", code, diag)
	}
}

func TestServerBindWrongPassword(t *testing.T) {
	srv := start(t)
	k := dial(t, srv)
	k.send(bindOp("CN=Kim Minji,OU=Students,"+base, "틀린것"))
	code, diag := resultOf(t, k.recv())
	if code != proto.ResultInvalidCredentials {
		t.Errorf("코드 = %d", code)
	}
	if !strings.Contains(diag, "data 52e") {
		t.Errorf("진단 = %q", diag)
	}
}

// 바인드 전에 검색하면 거절한다. 진짜 AD 도 익명 검색을 막아 두고,
// 그래서 Keycloak 에 서비스 계정을 적어 줘야 한다 (7부).
func TestServerSearchBeforeBindRejected(t *testing.T) {
	srv := start(t)
	k := dial(t, srv)
	k.send(searchOp(base, proto.ScopeWholeSubtree, "(objectClass=*)",
		nil, nil))
	res := k.recv()
	if res.OpNum() != proto.OpSearchResultDone {
		t.Fatalf("연산 = %d — 바로 Done 이 와야 한다", res.OpNum())
	}
	code, _ := resultOf(t, res)
	if code != proto.ResultInsufficientAccessRights {
		t.Errorf("코드 = %d, 원하는 것 50", code)
	}
}

// 한 연결에서 바인드를 다시 하면 그 뒤로는 새 신분이 된다.
func TestServerRebindChangesIdentity(t *testing.T) {
	srv := start(t)
	k := dial(t, srv)
	k.send(bindOp("CN=Kim Minji,OU=Students,"+base, "틀린것"))
	k.recv()
	// 실패한 바인드는 신분을 지운다 — 검색이 막혀야 한다.
	k.send(searchOp(base, proto.ScopeBaseObject, "(objectClass=*)", nil, nil))
	code, _ := resultOf(t, k.recv())
	if code != proto.ResultInsufficientAccessRights {
		t.Errorf("실패한 바인드 뒤인데 검색이 됐다: %d", code)
	}
	k.send(bindOp("CN=svc-keycloak,OU=Service Accounts,"+base,
		"Passw0rd!-demo"))
	if code, _ := resultOf(t, k.recv()); code != proto.ResultSuccess {
		t.Fatal("서비스 계정 바인드 실패")
	}
	k.send(searchOp(base, proto.ScopeBaseObject, "(objectClass=*)", nil, nil))
	if k.recv().OpNum() != proto.OpSearchResultEntry {
		t.Error("바인드 뒤인데 검색이 막혔다")
	}
}

// ── 검색 ─────────────────────────────────────────────────────────────

func bindSvc(t *testing.T, k *conn) {
	t.Helper()
	k.send(bindOp("CN=svc-keycloak,OU=Service Accounts,"+base,
		"Passw0rd!-demo"))
	if code, diag := resultOf(t, k.recv()); code != proto.ResultSuccess {
		t.Fatalf("서비스 계정 바인드 실패: %d %s", code, diag)
	}
}

// 검색의 답은 "찾은 것 여러 통 + 끝났다는 통 하나" 다.
func TestServerSearchEntriesThenDone(t *testing.T) {
	srv := start(t)
	k := dial(t, srv)
	bindSvc(t, k)
	k.send(searchOp(base, proto.ScopeWholeSubtree,
		"(&(objectClass=user)(sAMAccountName=minji))",
		[]string{"cn", "mail", "objectGUID"}, nil))

	res := k.recv()
	if res.OpNum() != proto.OpSearchResultEntry {
		t.Fatalf("첫 응답 = %d", res.OpNum())
	}
	kids, _ := ber.Children(res.Op.Value)
	if !strings.Contains(kids[0].Str(), "Kim Minji") {
		t.Errorf("찾은 DN = %s", kids[0].Str())
	}
	done := k.recv()
	if done.OpNum() != proto.OpSearchResultDone {
		t.Fatalf("둘째 응답 = %d", done.OpNum())
	}
	if code, _ := resultOf(t, done); code != proto.ResultSuccess {
		t.Errorf("Done 코드 = %d", code)
	}
}

// objectGUID 는 선을 타고 갈 때도 16바이트 그대로여야 한다.
func TestServerReturnsRawObjectGUID(t *testing.T) {
	srv := start(t)
	k := dial(t, srv)
	bindSvc(t, k)
	k.send(searchOp(base, proto.ScopeWholeSubtree,
		"(sAMAccountName=minji)", []string{"objectGUID"}, nil))
	res := k.recv()
	kids, _ := ber.Children(res.Op.Value)
	attrs, _ := ber.Children(kids[1].Value)
	if len(attrs) != 1 {
		t.Fatalf("속성 %d개", len(attrs))
	}
	one, _ := ber.Children(attrs[0].Value)
	vals, _ := ber.Children(one[1].Value)
	if len(vals) != 1 || len(vals[0].Value) != 16 {
		t.Fatalf("objectGUID 가 %d바이트", len(vals[0].Value))
	}
	if !bytes.Equal(vals[0].Value[:2], []byte{0x98, 0xD3}) {
		t.Errorf("앞머리 = % X", vals[0].Value[:4])
	}
	k.recv() // Done
}

// 비밀번호 칸은 선을 타고 나가면 안 된다 — 서버 단에서도 막혀야 한다.
func TestServerNeverSendsPassword(t *testing.T) {
	srv := start(t)
	k := dial(t, srv)
	bindSvc(t, k)
	k.send(searchOp(base, proto.ScopeWholeSubtree,
		"(sAMAccountName=minji)", nil, nil))
	res := k.recv()
	if bytes.Contains(res.Op.Value, []byte("Passw0rd")) {
		t.Error("응답 바이트 안에 비밀번호가 있다")
	}
	k.recv()
}

func TestServerSearchCountsBySize(t *testing.T) {
	srv := start(t)
	k := dial(t, srv)
	bindSvc(t, k)
	k.send(searchOp(base, proto.ScopeWholeSubtree, "(objectClass=user)",
		[]string{"cn"}, nil))
	n := 0
	for {
		res := k.recv()
		if res.OpNum() == proto.OpSearchResultDone {
			break
		}
		n++
	}
	if n != 7 {
		t.Errorf("사용자 %d명, 원하는 것 7", n)
	}
}

// 없는 base 로 물으면 noSuchObject(32) 다.
func TestServerSearchNoSuchObject(t *testing.T) {
	srv := start(t)
	k := dial(t, srv)
	bindSvc(t, k)
	k.send(searchOp("OU=없는곳,"+base, proto.ScopeWholeSubtree,
		"(objectClass=*)", nil, nil))
	code, _ := resultOf(t, k.recv())
	if code != proto.ResultNoSuchObject {
		t.Errorf("코드 = %d, 원하는 것 32", code)
	}
}

// ── 페이지 컨트롤 ────────────────────────────────────────────────────

// 페이지를 나눠 달라고 하면, 우리는 한 쪽에 다 담아 주고
// "다음 쪽은 없다"(빈 쿠키)고 답한다. Keycloak 은 그걸 보고 멈춘다.
func TestServerAnswersPagedControl(t *testing.T) {
	srv := start(t)
	k := dial(t, srv)
	bindSvc(t, k)
	pr := proto.PagedResults{Size: 2}
	ctl := proto.EncodeControl(proto.OIDPagedResults, false, pr.Encode())
	k.send(searchOp(base, proto.ScopeWholeSubtree, "(objectClass=user)",
		[]string{"cn"}, ctl))
	var done proto.Message
	for {
		res := k.recv()
		if res.OpNum() == proto.OpSearchResultDone {
			done = res
			break
		}
	}
	if len(done.Controls) != 1 {
		t.Fatalf("Done 에 컨트롤이 %d개", len(done.Controls))
	}
	back, err := proto.ParsePagedResults(done.Controls[0].Value)
	if err != nil {
		t.Fatal(err)
	}
	if len(back.Cookie) != 0 {
		t.Errorf("쿠키가 비어 있어야 한다: % X", back.Cookie)
	}
}

// 모르는 컨트롤에 criticality=TRUE 가 붙어 오면 거절해야 한다.
// "못 하겠으면 아예 하지 마라" 는 뜻이기 때문이다 (RFC 4511 §4.1.11).
func TestServerRejectsUnknownCriticalControl(t *testing.T) {
	srv := start(t)
	k := dial(t, srv)
	bindSvc(t, k)
	ctl := proto.EncodeControl("1.2.3.4.5.6.7", true, nil)
	k.send(searchOp(base, proto.ScopeBaseObject, "(objectClass=*)",
		nil, ctl))
	code, _ := resultOf(t, k.recv())
	if code != proto.ResultUnavailableCriticalExtension {
		t.Errorf("코드 = %d, 원하는 것 12", code)
	}
}

// ── 그 밖 ────────────────────────────────────────────────────────────

// 우리가 안 하는 연산(수정·추가·삭제)은 분명히 못 한다고 답한다.
func TestServerRejectsModify(t *testing.T) {
	srv := start(t)
	k := dial(t, srv)
	bindSvc(t, k)
	k.send(func(id int64) []byte {
		return ber.Seq(ber.Int(id),
			ber.Encode(ber.Tag(ber.Application, true, proto.OpModifyRequest),
				ber.Str("CN=Kim Minji,OU=Students,"+base)))
	})
	res := k.recv()
	code, _ := resultOf(t, res)
	if code != proto.ResultUnwillingToPerform {
		t.Errorf("코드 = %d, 원하는 것 53", code)
	}
}

// unbind 는 답이 없는 연산이다. 서버는 그냥 연결을 끊는다.
func TestServerUnbindClosesConnection(t *testing.T) {
	srv := start(t)
	k := dial(t, srv)
	bindSvc(t, k)
	k.send(func(id int64) []byte {
		return ber.Seq(ber.Int(id),
			ber.Encode(ber.Tag(ber.Application, false,
				proto.OpUnbindRequest), nil))
	})
	k.c.SetReadDeadline(time.Now().Add(3 * time.Second))
	buf := make([]byte, 16)
	if n, err := k.c.Read(buf); err == nil && n > 0 {
		t.Errorf("unbind 뒤에 %d바이트가 왔다", n)
	}
}

// 메시지를 반씩 나눠 보내도 서버가 이어 붙여 읽어야 한다.
// TCP 는 메시지 단위를 모른다 — 이걸 안 하면 어쩌다 한 번씩 실패한다.
func TestServerHandlesSplitWrites(t *testing.T) {
	srv := start(t)
	k := dial(t, srv)
	msg := bindOp("CN=Kim Minji,OU=Students,"+base, "Passw0rd!-demo")(1)
	half := len(msg) / 2
	if _, err := k.c.Write(msg[:half]); err != nil {
		t.Fatal(err)
	}
	time.Sleep(50 * time.Millisecond)
	if _, err := k.c.Write(msg[half:]); err != nil {
		t.Fatal(err)
	}
	if code, _ := resultOf(t, k.recv()); code != proto.ResultSuccess {
		t.Error("쪼개 보낸 메시지를 못 읽었다")
	}
}

// 말이 안 되는 바이트를 보내면 연결을 끊는다. 계속 받아 주면
// 그 뒤로 읽는 모든 것이 어긋난다.
func TestServerClosesOnGarbage(t *testing.T) {
	srv := start(t)
	k := dial(t, srv)
	k.c.Write([]byte{0x31, 0x02, 0x02, 0x01})
	k.c.SetReadDeadline(time.Now().Add(3 * time.Second))
	buf := make([]byte, 64)
	for {
		n, err := k.c.Read(buf)
		if err != nil {
			return // 끊겼다 — 바라던 대로
		}
		if n == 0 {
			return
		}
	}
}

// 로그는 덱에 그대로 실린다. 한 줄이 너무 길면 좁은 화면에서 옆으로 밀려
// 정작 봐야 할 결과가 안 보인다. 날짜는 파일 머리에 한 번만 적고
// 줄마다는 시각만 적는 것으로 그 폭을 줄였다.
func TestServerLogLinesAreNotTooWide(t *testing.T) {
	d, err := LoadLDIFFile("../../data/campus.ldif")
	if err != nil {
		t.Fatal(err)
	}
	var buf strings.Builder
	srv := NewServer(d, &buf)
	if err := srv.ListenPlain("127.0.0.1:0"); err != nil {
		t.Fatal(err)
	}
	defer srv.Close()
	k := dial(t, srv)
	// 이 덱에서 가장 긴 DN 으로 바인드한다
	k.send(bindOp("CN=svc-keycloak,OU=Service Accounts,"+base, "Passw0rd!-demo"))
	k.recv()
	k.send(searchOp(base, proto.ScopeWholeSubtree,
		"(&(objectClass=user)(sAMAccountName=minji))", []string{"cn"}, nil))
	k.recv()
	k.recv()
	k.c.Close()
	srv.Close()

	for _, line := range strings.Split(buf.String(), "\n") {
		if n := logCells(line); n > 108 {
			t.Errorf("%d칸짜리 로그 줄: %s", n, line)
		}
	}
	if !strings.Contains(buf.String(), "2026") &&
		!strings.Contains(buf.String(), "20") {
		t.Error("날짜를 어디에도 안 적었다")
	}
}

// Keycloak 의 User Federation 은 한 번에 여덟 개의 속성을 물어 온다.
// 그 목록을 한 줄에 몰면 140칸이 넘는다 — 4부의 캡처에서 실제로 그랬다.
func TestSearchLogFoldsLongAttrList(t *testing.T) {
	d, err := LoadLDIFFile("../../data/campus.ldif")
	if err != nil {
		t.Fatal(err)
	}
	var buf strings.Builder
	srv := NewServer(d, &buf)
	if err := srv.ListenPlain("127.0.0.1:0"); err != nil {
		t.Fatal(err)
	}
	defer srv.Close()
	k := dial(t, srv)
	k.send(bindOp("CN=svc-keycloak,OU=Service Accounts,"+base,
		"Passw0rd!-demo"))
	k.recv()
	// oidc/miniidp/directory.go 의 wantAttrs 와 같은 목록이다.
	k.send(searchOp(base, proto.ScopeWholeSubtree,
		"(&(objectClass=user)(sAMAccountName=minji))", []string{
			"distinguishedName", "sAMAccountName", "userPrincipalName",
			"cn", "displayName", "mail", "memberOf", "userAccountControl",
		}, nil))
	k.recv()
	k.recv()
	k.c.Close()
	srv.Close()

	log := buf.String()
	for _, line := range strings.Split(log, "\n") {
		if n := logCells(line); n > 108 {
			t.Errorf("%d칸짜리 로그 줄: %s", n, line)
		}
	}
	// 접혔어도 속목록은 다 남아 있어야 한다 — 접는다고 잘라 버리면
	// 로그를 읽는 사람이 무엇을 물었는지 알 수 없다.
	for _, a := range []string{"distinguishedName", "userAccountControl",
		"memberOf"} {
		if !strings.Contains(log, a) {
			t.Errorf("%q 가 로그에서 사라졌다", a)
		}
	}
}

// 진짜 Keycloak 이 보내는 필터는 길다. 사용자를 찾을 때만 해도
// objectClass 를 셋이나 겹쳐 묻고, 그룹을 뒤질 때는 DN 을 통째로 싣는다.
// 실제로 128칸짜리 줄이 나왔다 — 접지 않으면 좁은 화면에서 잘린다.
func TestSearchLogFoldsLongFilter(t *testing.T) {
	d, err := LoadLDIFFile("../../data/campus.ldif")
	if err != nil {
		t.Fatal(err)
	}
	var buf strings.Builder
	srv := NewServer(d, &buf)
	if err := srv.ListenPlain("127.0.0.1:0"); err != nil {
		t.Fatal(err)
	}
	defer srv.Close()
	k := dial(t, srv)
	k.send(bindOp("CN=svc-keycloak,OU=Service Accounts,"+base,
		"Passw0rd!-demo"))
	k.recv()
	// Keycloak 이 실제로 보낸 필터다 (out/kc_fakead.log 에서 옮겼다).
	k.send(searchOp(base, proto.ScopeWholeSubtree,
		"(&(sAMAccountName=minji)(objectclass=person)"+
			"(objectclass=organizationalPerson)(objectclass=user))",
		[]string{"cn"}, nil))
	k.recv()
	k.recv()
	k.c.Close()
	srv.Close()

	log := buf.String()
	for _, line := range strings.Split(log, "\n") {
		if n := logCells(line); n > 108 {
			t.Errorf("%d칸짜리 로그 줄: %s", n, line)
		}
	}
	// 접혔어도 필터는 다 남아 있어야 한다.
	for _, want := range []string{"sAMAccountName=minji",
		"organizationalPerson"} {
		if !strings.Contains(log, want) {
			t.Errorf("%q 가 로그에서 사라졌다", want)
		}
	}
}

func logCells(s string) int {
	n := 0
	for _, r := range s {
		if (r >= 0xAC00 && r <= 0xD7A3) || (r >= 0x3000 && r <= 0x303F) ||
			(r >= 0x4E00 && r <= 0x9FFF) || (r >= 0xFF00 && r <= 0xFF60) {
			n += 2
		} else {
			n++
		}
	}
	return n
}

// ── LDAPS ────────────────────────────────────────────────────────────

// 636 쪽 문은 처음부터 TLS 다. StartTLS 와 헷갈리지 말 것 — 그쪽은 389
// 로 붙은 뒤 도중에 암호화로 바꾸는 방식이고, 우리는 안 한다.
func TestServerLDAPS(t *testing.T) {
	d, err := LoadLDIFFile("../../data/campus.ldif")
	if err != nil {
		t.Fatal(err)
	}
	srv := NewServer(d, io.Discard)
	err = srv.ListenTLS("127.0.0.1:0",
		"../../certs/ldap.crt", "../../certs/ldap.key")
	if err != nil {
		t.Fatalf("LDAPS 를 못 연다: %v", err)
	}
	defer srv.Close()

	pem, err := os.ReadFile("../../certs/demo-ca.crt")
	if err != nil {
		t.Fatal(err)
	}
	pool := x509.NewCertPool()
	pool.AppendCertsFromPEM(pem)

	c, err := tls.Dial("tcp", srv.TLSAddr(), &tls.Config{
		RootCAs: pool, ServerName: "ldap.ad.campus.example",
	})
	if err != nil {
		t.Fatalf("TLS 악수 실패: %v", err)
	}
	defer c.Close()

	k := &conn{t: t, c: c}
	k.send(bindOp("CN=Kim Minji,OU=Students,"+base, "Passw0rd!-demo"))
	if code, _ := resultOf(t, k.recv()); code != proto.ResultSuccess {
		t.Error("LDAPS 위에서 바인드 실패")
	}
}

// 우리 CA 를 안 믿으면 악수가 깨진다 — 7부 truststore 이야기의 뿌리다.
func TestServerLDAPSRejectsUnknownCA(t *testing.T) {
	d, _ := LoadLDIFFile("../../data/campus.ldif")
	srv := NewServer(d, io.Discard)
	if err := srv.ListenTLS("127.0.0.1:0",
		"../../certs/ldap.crt", "../../certs/ldap.key"); err != nil {
		t.Fatal(err)
	}
	defer srv.Close()
	_, err := tls.Dial("tcp", srv.TLSAddr(), &tls.Config{
		ServerName: "ldap.ad.campus.example",
	})
	if err == nil {
		t.Fatal("모르는 CA 인데 붙었다")
	}
}

func resultOf(t *testing.T, m proto.Message) (int, string) {
	t.Helper()
	kids, err := ber.Children(m.Op.Value)
	if err != nil || len(kids) < 3 {
		t.Fatalf("결과 칸을 못 읽는다: %v", err)
	}
	code, _ := kids[0].Int()
	return int(code), kids[2].Str()
}
