package proto

import (
	"bytes"
	"encoding/hex"
	"strings"
	"testing"

	"treasure/keycloak_ad/ldap/ber"
)

func hx(t *testing.T, s string) []byte {
	t.Helper()
	b, err := hex.DecodeString(strings.ReplaceAll(s, " ", ""))
	if err != nil {
		t.Fatalf("시험 벡터가 잘못됐다: %v", err)
	}
	return b
}

// ── 메시지 껍데기 ────────────────────────────────────────────────────

func TestParseAnonymousBind(t *testing.T) {
	msg, err := ParseMessage(hx(t,
		"30 0C 02 01 01 60 07 02 01 03 04 00 80 00"))
	if err != nil {
		t.Fatal(err)
	}
	if msg.ID != 1 {
		t.Errorf("messageID = %d", msg.ID)
	}
	if msg.OpNum() != OpBindRequest {
		t.Fatalf("연산 = %d, 원하는 것 %d", msg.OpNum(), OpBindRequest)
	}
	br, err := ParseBindRequest(msg.Op)
	if err != nil {
		t.Fatal(err)
	}
	if br.Version != 3 || br.Name != "" || br.Password != "" {
		t.Errorf("바인드 = %+v", br)
	}
	if !br.Simple {
		t.Error("simple 인증이어야 한다")
	}
}

func TestParseSimpleBindWithDN(t *testing.T) {
	dn := "CN=svc-keycloak,OU=Service Accounts," +
		"DC=ad,DC=campus,DC=example"
	raw := ber.Seq(
		ber.Int(2),
		ber.Encode(ber.Tag(ber.Application, true, OpBindRequest),
			cat(ber.Int(3), ber.Str(dn),
				ber.Encode(ber.Tag(ber.Context, false, 0),
					[]byte("Passw0rd!-demo")))),
	)
	msg, err := ParseMessage(raw)
	if err != nil {
		t.Fatal(err)
	}
	br, err := ParseBindRequest(msg.Op)
	if err != nil {
		t.Fatal(err)
	}
	if br.Name != dn {
		t.Errorf("DN = %q", br.Name)
	}
	if br.Password != "Passw0rd!-demo" {
		t.Errorf("비밀번호 = %q", br.Password)
	}
}

// SASL 로 오면 우리는 못 한다고 답해야 한다. 조용히 simple 로 처리하면
// 비밀번호 없이 통과시키는 셈이 된다.
func TestParseBindRejectsSASL(t *testing.T) {
	raw := ber.Encode(ber.Tag(ber.Application, true, OpBindRequest),
		cat(ber.Int(3), ber.Str(""),
			ber.Encode(ber.Tag(ber.Context, true, 3),
				cat(ber.Str("GSSAPI")))))
	tlv, _, _ := ber.Next(raw)
	br, err := ParseBindRequest(tlv)
	if err == nil && br.Simple {
		t.Error("SASL 인데 simple 로 읽혔다")
	}
}

func TestParseMessageRejectsGarbage(t *testing.T) {
	for _, c := range []string{
		"",
		"30 02 02 01", // 내용이 모자란다
		"31 0C 02 01 01 60 07 02 01 03 04 00 80 00", // SET 으로 왔다
		"30 03 04 01 41", // messageID 가 정수가 아니다
		"30 03 02 01 01", // 연산이 없다
	} {
		if _, err := ParseMessage(hx(t, c)); err == nil {
			t.Errorf("%q: 오류가 나야 한다", c)
		}
	}
}

// ── 필터 ─────────────────────────────────────────────────────────────

// 진짜 바이트로 못 박아 둔다. 여기가 어긋나면 Keycloak 이 우리를 이해
// 못 한다.
func TestFilterGoldenBytes(t *testing.T) {
	cases := []struct {
		text string
		hex  string
	}{
		{"(cn=minji)", "A3 0B 04 02 63 6E 04 05 6D 69 6E 6A 69"},
		{"(objectClass=*)",
			"87 0B 6F 62 6A 65 63 74 43 6C 61 73 73"},
		{"(&(a=1)(b=2))",
			"A0 10 A3 06 04 01 61 04 01 31 A3 06 04 01 62 04 01 32"},
	}
	for _, c := range cases {
		f, err := ParseFilterString(c.text)
		if err != nil {
			t.Fatalf("%s: %v", c.text, err)
		}
		got := EncodeFilter(f)
		if !bytes.Equal(got, hx(t, c.hex)) {
			t.Errorf("%s\n  = % X\n  원하는 것 %s", c.text, got, c.hex)
		}
	}
}

// 글 → 나무 → 바이트 → 나무 → 글 을 돌아 제자리에 와야 한다.
func TestFilterRoundTrip(t *testing.T) {
	texts := []string{
		"(cn=minji)",
		"(objectClass=*)",
		"(!(cn=minji))",
		"(&(objectClass=user)(sAMAccountName=minji))",
		"(|(cn=minji)(cn=prof.kim)(cn=admin.lee))",
		"(&(objectClass=person)(objectClass=organizationalPerson)" +
			"(objectClass=user)(sAMAccountName=minji))",
		"(cn=min*)",
		"(cn=*ji)",
		"(cn=m*n*i)",
		"(cn=*)",
		"(uidNumber>=1000)",
		"(uidNumber<=2000)",
		"(cn~=minji)",
		"(&(a=1)(|(b=2)(!(c=3))))",
		"(memberOf=CN=lunch-users,OU=Groups,DC=ad,DC=campus)",
	}
	for _, want := range texts {
		f, err := ParseFilterString(want)
		if err != nil {
			t.Fatalf("%s: 글을 못 읽는다: %v", want, err)
		}
		if got := f.String(); got != want {
			t.Errorf("글→나무→글: %s → %s", want, got)
		}
		tlv, _, err := ber.Next(EncodeFilter(f))
		if err != nil {
			t.Fatalf("%s: %v", want, err)
		}
		back, err := ParseFilter(tlv)
		if err != nil {
			t.Fatalf("%s: 바이트를 못 읽는다: %v", want, err)
		}
		if got := back.String(); got != want {
			t.Errorf("바이트→나무→글: %s → %s", want, got)
		}
	}
}

// RFC 4515 §3 — 값 안의 ( ) * \ 와 0x00 은 \XX 로 적는다.
// 이걸 안 하면 값에 괄호 하나를 넣어 필터를 통째로 바꿀 수 있다.
func TestFilterEscaping(t *testing.T) {
	cases := []struct{ raw, text string }{
		{"a*b", `(cn=a\2ab)`},
		{"a(b", `(cn=a\28b)`},
		{"a)b", `(cn=a\29b)`},
		{`a\b`, `(cn=a\5cb)`},
		{"a\x00b", `(cn=a\00b)`},
	}
	for _, c := range cases {
		f := &Equal{Attr: "cn", Value: c.raw}
		if got := f.String(); got != c.text {
			t.Errorf("%q → %s, 원하는 것 %s", c.raw, got, c.text)
		}
		back, err := ParseFilterString(c.text)
		if err != nil {
			t.Fatalf("%s: %v", c.text, err)
		}
		if eq, ok := back.(*Equal); !ok || eq.Value != c.raw {
			t.Errorf("%s 를 되읽으니 %#v", c.text, back)
		}
	}
}

func TestFilterStringRejectsBad(t *testing.T) {
	for _, s := range []string{
		"", "cn=minji", "(cn=minji", "cn=minji)", "(&)",
		"(!(a=1)(b=2))",
		"(cn)", "()", "(&(a=1)", "(cn=a\\2)",
	} {
		if _, err := ParseFilterString(s); err == nil {
			t.Errorf("%q: 오류가 나야 한다", s)
		}
	}
}

// ── 검색 요청 ────────────────────────────────────────────────────────

func TestParseSearchRequest(t *testing.T) {
	base := "DC=ad,DC=campus,DC=example"
	f, _ := ParseFilterString("(sAMAccountName=minji)")
	raw := ber.Encode(ber.Tag(ber.Application, true, OpSearchRequest),
		cat(ber.Str(base), ber.Enum(int64(ScopeWholeSubtree)),
			ber.Enum(0), ber.Int(500), ber.Int(30), ber.Bool(false),
			EncodeFilter(f),
			ber.Seq(ber.Str("cn"), ber.Str("mail"))))
	tlv, _, _ := ber.Next(raw)
	sr, err := ParseSearchRequest(tlv)
	if err != nil {
		t.Fatal(err)
	}
	if sr.BaseDN != base {
		t.Errorf("base = %q", sr.BaseDN)
	}
	if sr.Scope != ScopeWholeSubtree {
		t.Errorf("scope = %d", sr.Scope)
	}
	if sr.SizeLimit != 500 || sr.TimeLimit != 30 || sr.TypesOnly {
		t.Errorf("한계 = %+v", sr)
	}
	if sr.Filter.String() != "(sAMAccountName=minji)" {
		t.Errorf("필터 = %s", sr.Filter.String())
	}
	if len(sr.Attrs) != 2 || sr.Attrs[0] != "cn" ||
		sr.Attrs[1] != "mail" {
		t.Errorf("속성 = %v", sr.Attrs)
	}
}

func TestScopeNames(t *testing.T) {
	cases := map[int]string{
		ScopeBaseObject: "base", ScopeSingleLevel: "one",
		ScopeWholeSubtree: "sub",
	}
	for k, want := range cases {
		if got := ScopeName(k); got != want {
			t.Errorf("ScopeName(%d) = %q, 원하는 것 %q", k, got, want)
		}
	}
	if ScopeName(9) == "" {
		t.Error("모르는 scope 도 뭐라고는 말해야 한다")
	}
}

// ── 응답 ─────────────────────────────────────────────────────────────

func TestBindResponseRoundTrip(t *testing.T) {
	raw := BindResponse(7, ResultInvalidCredentials, "",
		"80090308: LdapErr: DSID-0C09042F, data 52e")
	msg, err := ParseMessage(raw)
	if err != nil {
		t.Fatal(err)
	}
	if msg.ID != 7 {
		t.Errorf("messageID = %d", msg.ID)
	}
	if msg.OpNum() != OpBindResponse {
		t.Errorf("연산 = %d", msg.OpNum())
	}
	kids, err := ber.Children(msg.Op.Value)
	if err != nil || len(kids) < 3 {
		t.Fatalf("자식 %d개: %v", len(kids), err)
	}
	code, _ := kids[0].Int()
	if code != ResultInvalidCredentials {
		t.Errorf("결과 코드 = %d", code)
	}
	if !strings.Contains(kids[2].Str(), "data 52e") {
		t.Errorf("진단 문구 = %q", kids[2].Str())
	}
}

func TestSearchResultEntryKeepsBinaryValues(t *testing.T) {
	guid := []byte{0x00, 0x11, 0x22, 0x00, 0xFF, 0xEE, 0x00, 0x99,
		0x88, 0x77, 0x66, 0x55, 0x44, 0x33, 0x22, 0x11}
	raw := SearchResultEntry(3, "CN=minji,DC=ad",
		[]Attribute{{Name: "objectGUID", Values: [][]byte{guid}}})
	msg, err := ParseMessage(raw)
	if err != nil {
		t.Fatal(err)
	}
	kids, _ := ber.Children(msg.Op.Value)
	attrs, _ := ber.Children(kids[1].Value)
	one, _ := ber.Children(attrs[0].Value)
	vals, _ := ber.Children(one[1].Value)
	if !bytes.Equal(vals[0].Value, guid) {
		t.Errorf("objectGUID 가 바뀌었다: % X", vals[0].Value)
	}
}

func TestResultName(t *testing.T) {
	if ResultName(ResultSuccess) != "success" {
		t.Error("0 은 success 여야 한다")
	}
	if !strings.Contains(ResultName(ResultInvalidCredentials),
		"invalidCredentials") {
		t.Errorf("49 = %q", ResultName(ResultInvalidCredentials))
	}
	if ResultName(222) == "" {
		t.Error("모르는 코드도 뭐라고는 말해야 한다")
	}
}

// ── 페이지 컨트롤 (AD 가 1000건에서 끊어서 꼭 필요하다) ────────

func TestPagedResultsRoundTrip(t *testing.T) {
	want := PagedResults{Size: 500, Cookie: []byte{0x01, 0x02, 0x03}}
	got, err := ParsePagedResults(want.Encode())
	if err != nil {
		t.Fatal(err)
	}
	if got.Size != want.Size || !bytes.Equal(got.Cookie, want.Cookie) {
		t.Errorf("%+v → %+v", want, got)
	}
}

func TestControlsParsed(t *testing.T) {
	pr := PagedResults{Size: 1000}
	raw := ber.Seq(
		ber.Int(4),
		ber.Encode(ber.Tag(ber.Application, true, OpSearchRequest),
			ber.Str("dummy")),
		ber.Encode(ber.Tag(ber.Context, true, 0),
			EncodeControl(OIDPagedResults, true, pr.Encode())),
	)
	msg, err := ParseMessage(raw)
	if err != nil {
		t.Fatal(err)
	}
	if len(msg.Controls) != 1 {
		t.Fatalf("컨트롤 %d개", len(msg.Controls))
	}
	c := msg.Controls[0]
	if c.OID != OIDPagedResults || !c.Critical {
		t.Errorf("컨트롤 = %+v", c)
	}
	back, err := ParsePagedResults(c.Value)
	if err != nil || back.Size != 1000 {
		t.Errorf("풀어 보니 %+v (%v)", back, err)
	}
}

func cat(parts ...[]byte) []byte {
	var out []byte
	for _, p := range parts {
		out = append(out, p...)
	}
	return out
}

// objectGUID 는 16바이트 이진값이다(3부 2장). Keycloak 은 사용자를
// 다시 찾을 때 그 값을 **필터에 그대로** 싣는다 — 진짜로 그렇게 한다.
//
// 그 바이트를 날것으로 적으면 로그도 화면도 깨진다. RFC 4515 §3 은
// 꼭 escape 해야 할 것을 다섯 개만 정했지만, 더 escape 해도 된다고
// 적어 두었다(§3 의 valueencoding). 실제 도구들도 그렇게 한다.
func TestFilterEscapesBinaryValue(t *testing.T) {
	guid := string([]byte{0x98, 0x08, 0xd3, 0x98, 0x8b, 0x6d, 0x12, 0xdc,
		0x27, 0x95, 0xb5, 0x5f, 0x90, 0xa0, 0xaa, 0x29})
	f := &Equal{Attr: "objectGUID", Value: guid}
	got := f.String()

	for _, b := range []byte(got) {
		if b < 0x20 || b > 0x7e {
			t.Fatalf("화면에 못 쓰는 바이트 %#x 가 남아 있다: %q", b, got)
		}
	}
	// 볼 수 있는 글자는 그대로 둔다. 0x6d 는 'm', 0x27 은 작은따옴표라
	// 감싸지 않는다 — ldapsearch 와 Keycloak 의 로그도 이렇게 적는다.
	// 이진값이 반쯤 글자로 보이는 것이 오히려 진짜 모습이다.
	// (0x29 는 ')' 라 §3 이 반드시 감싸라고 정한 다섯에 든다)
	want := "(objectGUID=\\98\\08\\d3\\98\\8bm\\12\\dc" +
		"'\\95\\b5_\\90\\a0\\aa\\29)"
	if got != want {
		t.Errorf("\n받은 것: %s\n원하는 것: %s", got, want)
	}
}

// 글자로 된 값은 그대로 남아야 한다 — 다 escape 해 버리면 못 읽는다.
func TestFilterKeepsPrintableValue(t *testing.T) {
	f := &Equal{Attr: "sAMAccountName", Value: "minji"}
	if got := f.String(); got != "(sAMAccountName=minji)" {
		t.Errorf("%s", got)
	}
}
