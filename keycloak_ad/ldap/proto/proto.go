// proto — LDAP 메시지와 검색 필터.
//
// ber 가 "바이트를 어떻게 싸는가" 였다면 여기는 "무슨 말을 하는가" 다.
// LDAP 의 모든 메시지는 같은 봉투에 들어 있다.
//
//	LDAPMessage ::= SEQUENCE {
//	  messageID  INTEGER,        -- 이 답이 어느 물음에 대한 것인지
//	  protocolOp CHOICE { … },   -- 실제 용건
//	  controls   [0] SEQUENCE OF Control OPTIONAL }
//
// messageID 가 있는 이유는 LDAP 이 한 연결에서 여러 물음을 동시에 던질
// 수 있기 때문이다. 답은 순서대로 오지 않아도 되고, 번호로 짝을 맞춘다.
//
// 필터는 나무(tree)다. (&(a=1)(b=2)) 는 "그리고" 마디 아래 잎 둘이다.
// 이 파일은 그 나무를 세 가지 모습으로 오간다 —
// 사람이 읽는 글(RFC 4515) · 우리 안의 나무 · 선을 타고 가는 바이트.
package proto

import (
	"errors"
	"fmt"
	"strings"

	"treasure/keycloak_ad/ldap/ber"
)

// protocolOp 의 [APPLICATION n] 번호. RFC 4511 §4.2~4.5.
const (
	OpBindRequest       = 0
	OpBindResponse      = 1
	OpUnbindRequest     = 2
	OpSearchRequest     = 3
	OpSearchResultEntry = 4
	OpSearchResultDone  = 5
	OpModifyRequest     = 6
	OpAddRequest        = 8
	OpDelRequest        = 10
	OpExtendedRequest   = 23
	OpExtendedResponse  = 24
)

// 검색 범위. "어디부터 어디까지 뒤질 것인가".
const (
	ScopeBaseObject   = 0 // 그 하나만
	ScopeSingleLevel  = 1 // 바로 아래 한 층만
	ScopeWholeSubtree = 2 // 그 아래 전부
)

func ScopeName(n int) string {
	switch n {
	case ScopeBaseObject:
		return "base"
	case ScopeSingleLevel:
		return "one"
	case ScopeWholeSubtree:
		return "sub"
	}
	return fmt.Sprintf("알 수 없음(%d)", n)
}

// 결과 코드. 이 덱에서 실제로 만나는 것만 이름을 붙였다 (RFC 4511 부록
// A).
const (
	ResultSuccess                      = 0
	ResultOperationsError              = 1
	ResultProtocolError                = 2
	ResultTimeLimitExceeded            = 3
	ResultSizeLimitExceeded            = 4
	ResultAuthMethodNotSupported       = 7
	ResultStrongerAuthRequired         = 8
	ResultUnavailableCriticalExtension = 12
	ResultNoSuchObject                 = 32
	ResultInvalidDNSyntax              = 34
	ResultInvalidCredentials           = 49
	ResultInsufficientAccessRights     = 50
	ResultUnwillingToPerform           = 53
)

var resultNames = map[int]string{
	ResultSuccess:                      "success",
	ResultOperationsError:              "operationsError",
	ResultProtocolError:                "protocolError",
	ResultTimeLimitExceeded:            "timeLimitExceeded",
	ResultSizeLimitExceeded:            "sizeLimitExceeded",
	ResultAuthMethodNotSupported:       "authMethodNotSupported",
	ResultStrongerAuthRequired:         "strongerAuthRequired",
	ResultUnavailableCriticalExtension: "unavailableCriticalExtension",
	ResultNoSuchObject:                 "noSuchObject",
	ResultInvalidDNSyntax:              "invalidDNSyntax",
	ResultInvalidCredentials:           "invalidCredentials",
	ResultInsufficientAccessRights:     "insufficientAccessRights",
	ResultUnwillingToPerform:           "unwillingToPerform",
}

// ResultName 은 이름만 돌려준다. 번호까지 함께 보이고 싶으면 부르는
// 쪽에서 붙인다 — 로그마다 원하는 모양이 달라서, 여기서 섞어 두면
// 되돌릴 수 없다.
func ResultName(n int) string {
	if s, ok := resultNames[n]; ok {
		return s
	}
	return fmt.Sprintf("알 수 없음(%d)", n)
}

// ── 봉투 ─────────────────────────────────────────────────────────────

// Control 은 "이 연산을 이렇게 처리해 달라" 는 곁가지 부탁이다.
// 이 덱에서 쓰는 것은 페이지 나누기 하나뿐이다.
type Control struct {
	OID      string
	Critical bool // 참이면 "못 하겠으면 아예 거절해라"
	Value    []byte
}

type Message struct {
	ID       int64
	Op       ber.TLV
	Controls []Control
}

// OpNum 은 protocolOp 의 [APPLICATION n] 번호다.
func (m Message) OpNum() int { return m.Op.Num() }

func ParseMessage(b []byte) (Message, error) {
	tlv, rest, err := ber.Next(b)
	if err != nil {
		return Message{}, err
	}
	if len(rest) != 0 {
		return Message{}, fmt.Errorf("메시지 뒤에 %d바이트가 남았다",
			len(rest))
	}
	if tlv.Tag != ber.TagSequence {
		return Message{}, fmt.Errorf(
			"LDAPMessage 는 SEQUENCE(0x30)여야 한다 — 받은 것 0x%02X",
			tlv.Tag)
	}
	kids, err := ber.Children(tlv.Value)
	if err != nil {
		return Message{}, err
	}
	if len(kids) < 2 {
		return Message{}, errors.New("messageID 와 연산이 필요하다")
	}
	if kids[0].Tag != ber.TagInteger {
		return Message{}, errors.New("messageID 가 INTEGER 가 아니다")
	}
	id, err := kids[0].Int()
	if err != nil {
		return Message{}, err
	}
	m := Message{ID: id, Op: kids[1]}
	// 컨트롤은 [0] 로 감싸여 맨 뒤에 온다. 없을 수도 있다.
	for _, k := range kids[2:] {
		if k.Tag != ber.Tag(ber.Context, true, 0) {
			continue
		}
		cs, err := ber.Children(k.Value)
		if err != nil {
			return Message{}, err
		}
		for _, c := range cs {
			ctl, err := parseControl(c)
			if err != nil {
				return Message{}, err
			}
			m.Controls = append(m.Controls, ctl)
		}
	}
	return m, nil
}

func parseControl(t ber.TLV) (Control, error) {
	kids, err := ber.Children(t.Value)
	if err != nil || len(kids) == 0 {
		return Control{}, errors.New("컨트롤에 OID 가 없다")
	}
	c := Control{OID: kids[0].Str()}
	for _, k := range kids[1:] {
		switch k.Tag {
		case ber.TagBoolean:
			c.Critical, _ = k.Bool()
		case ber.TagOctetString:
			c.Value = k.Value
		}
	}
	return c, nil
}

// EncodeControl 은 컨트롤 하나를 싼다. criticality 는 거짓이면 관례상
// 뺀다.
func EncodeControl(oid string, critical bool, value []byte) []byte {
	parts := [][]byte{ber.Str(oid)}
	if critical {
		parts = append(parts, ber.Bool(true))
	}
	if value != nil {
		parts = append(parts, ber.Bytes(value))
	}
	return ber.Seq(parts...)
}

// ── 바인드 ───────────────────────────────────────────────────────────

// BindRequest 는 "나는 이 사람이고 비밀번호는 이것이다" 다.
//
// 이름이 비어 있고 비밀번호도 비어 있으면 익명 바인드다. AD 는 보통
// 익명을 막아 두는데, 그 설정이 7부에서 "서비스 계정이 왜 필요한가" 로
// 이어진다.
type BindRequest struct {
	Version  int64
	Name     string // 바인드 DN
	Password string
	Simple   bool // 거짓이면 SASL — 우리는 못 한다고 답한다
}

func ParseBindRequest(t ber.TLV) (BindRequest, error) {
	kids, err := ber.Children(t.Value)
	if err != nil {
		return BindRequest{}, err
	}
	if len(kids) < 3 {
		return BindRequest{}, errors.New("BindRequest 의 칸이 모자란다")
	}
	ver, err := kids[0].Int()
	if err != nil {
		return BindRequest{}, err
	}
	br := BindRequest{Version: ver, Name: kids[1].Str()}
	auth := kids[2]
	switch auth.Tag {
	case ber.Tag(ber.Context, false, 0): // simple
		br.Simple = true
		br.Password = string(auth.Value)
	default:
		// [3] 이면 SASL 이다. 우리는 흉내 내지 않는다 — 3부에서
		// "Kerberos 는 무엇인가" 를 개념으로만 다루는 이유가 이것이다.
		return br, fmt.Errorf(
			"simple 인증만 지원한다 — 받은 방식 태그 0x%02X", auth.Tag)
	}
	return br, nil
}

// ── 검색 ─────────────────────────────────────────────────────────────

type SearchRequest struct {
	BaseDN    string
	Scope     int
	Deref     int
	SizeLimit int64
	TimeLimit int64
	TypesOnly bool // 참이면 값 없이 속성 이름만 달라는 뜻
	Filter    Filter
	Attrs     []string // 비어 있으면 "전부 달라"
}

func ParseSearchRequest(t ber.TLV) (SearchRequest, error) {
	kids, err := ber.Children(t.Value)
	if err != nil {
		return SearchRequest{}, err
	}
	if len(kids) < 8 {
		return SearchRequest{}, fmt.Errorf(
			"SearchRequest 의 칸이 %d개 — 8개여야 한다", len(kids))
	}
	scope, err := kids[1].Int()
	if err != nil {
		return SearchRequest{}, err
	}
	deref, _ := kids[2].Int()
	size, err := kids[3].Int()
	if err != nil {
		return SearchRequest{}, err
	}
	tl, err := kids[4].Int()
	if err != nil {
		return SearchRequest{}, err
	}
	typesOnly, err := kids[5].Bool()
	if err != nil {
		return SearchRequest{}, err
	}
	f, err := ParseFilter(kids[6])
	if err != nil {
		return SearchRequest{}, err
	}
	var attrs []string
	list, err := ber.Children(kids[7].Value)
	if err != nil {
		return SearchRequest{}, err
	}
	for _, a := range list {
		attrs = append(attrs, a.Str())
	}
	return SearchRequest{
		BaseDN: kids[0].Str(), Scope: int(scope), Deref: int(deref),
		SizeLimit: size, TimeLimit: tl, TypesOnly: typesOnly,
		Filter: f, Attrs: attrs,
	}, nil
}

// ── 응답 ─────────────────────────────────────────────────────────────

// Attribute 는 값이 [][]byte 다. 글자가 아니라 바이트인 것이 중요하다 —
// objectGUID 16바이트가 그대로 실려야 하기 때문이다(7부).
type Attribute struct {
	Name   string
	Values [][]byte
}

// ldapResult 는 성공·실패를 알리는 세 칸이다. 여러 응답이 이걸
// 공유한다.
//
//	resultCode · matchedDN · diagnosticMessage
//
// AD 는 diagnosticMessage 에 "data 52e" 같은 힌트를 넣는다.
// 7부의 진단이 그 문자열을 읽는 데서 시작한다.
func ldapResult(code int, matchedDN, diag string) [][]byte {
	return [][]byte{
		ber.Enum(int64(code)), ber.Str(matchedDN), ber.Str(diag)}
}

func BindResponse(id int64, code int, matchedDN, diag string) []byte {
	return ber.Seq(ber.Int(id),
		ber.Encode(ber.Tag(ber.Application, true, OpBindResponse),
			concat(ldapResult(code, matchedDN, diag))))
}

func SearchResultEntry(id int64, dn string, attrs []Attribute) []byte {
	var list [][]byte
	for _, a := range attrs {
		var vals [][]byte
		for _, v := range a.Values {
			vals = append(vals, ber.Bytes(v))
		}
		list = append(list, ber.Seq(ber.Str(a.Name), ber.Set(vals...)))
	}
	return ber.Seq(ber.Int(id),
		ber.Encode(ber.Tag(ber.Application, true, OpSearchResultEntry),
			concat([][]byte{ber.Str(dn), ber.Seq(list...)})))
}

// SearchResultDone 은 "그 검색은 여기까지" 다. 컨트롤을 함께 실어 보낼
// 수 있는데, 페이지 나누기의 다음 쪽 표(cookie)가 이 자리로 온다.
func SearchResultDone(id int64, code int, matchedDN, diag string,
	controls ...[]byte) []byte {
	parts := [][]byte{
		ber.Int(id),
		ber.Encode(ber.Tag(ber.Application, true, OpSearchResultDone),
			concat(ldapResult(code, matchedDN, diag))),
	}
	if len(controls) > 0 {
		parts = append(parts,
			ber.Encode(ber.Tag(ber.Context, true, 0), concat(controls)))
	}
	return ber.Seq(parts...)
}

func concat(parts [][]byte) []byte {
	var out []byte
	for _, p := range parts {
		out = append(out, p...)
	}
	return out
}

// ── 페이지 나누기 컨트롤 ─────────────────────────────────────────────

// OIDPagedResults 는 Simple Paged Results (RFC 2696).
// 마이크로소프트가 정한 번호라 1.2.840.113556 으로 시작한다.
//
// 왜 반드시 필요한가: AD 는 한 번의 검색에서 기본 1000건까지만 돌려주고
// 나머지를 그냥 버린다. 사용자가 1000명을 넘는 순간, 페이지를 안 쓰면
// 뒤쪽 사람들이 조용히 사라진다. 7부에서 "동기화했는데 일부만 왔다" 는
// 사고의 정체가 이것이다.
const OIDPagedResults = "1.2.840.113556.1.4.319"

type PagedResults struct {
	Size   int64  // 한 쪽에 몇 건
	Cookie []byte // 서버가 준 "다음 쪽 표". 비어 있으면 마지막 쪽
}

func (p PagedResults) Encode() []byte {
	return ber.Seq(ber.Int(p.Size), ber.Bytes(p.Cookie))
}

func ParsePagedResults(v []byte) (PagedResults, error) {
	tlv, _, err := ber.Next(v)
	if err != nil {
		return PagedResults{}, err
	}
	kids, err := ber.Children(tlv.Value)
	if err != nil || len(kids) < 2 {
		return PagedResults{}, errors.New("페이지 컨트롤의 칸이 부족")
	}
	size, err := kids[0].Int()
	if err != nil {
		return PagedResults{}, err
	}
	return PagedResults{Size: size, Cookie: kids[1].Value}, nil
}

// ── 필터: 나무 ───────────────────────────────────────────────────────

// Filter 는 검색 조건 나무의 마디다. String() 은 RFC 4515 의 글로
// 되돌린다.
type Filter interface{ String() string }

type And struct{ Subs []Filter }
type Or struct{ Subs []Filter }
type Not struct{ Sub Filter }
type Equal struct{ Attr, Value string }
type Present struct{ Attr string }
type GreaterOrEqual struct{ Attr, Value string }
type LessOrEqual struct{ Attr, Value string }
type Approx struct{ Attr, Value string }

// Substrings 는 별표가 낀 조건이다. (cn=m*n*i) 면
// Initial="m", Any=["n"], Final="i".
type Substrings struct {
	Attr    string
	Initial string
	Any     []string
	Final   string
}

func joinSubs(op string, subs []Filter) string {
	var b strings.Builder
	b.WriteString("(" + op)
	for _, s := range subs {
		b.WriteString(s.String())
	}
	b.WriteString(")")
	return b.String()
}

func (f *And) String() string { return joinSubs("&", f.Subs) }
func (f *Or) String() string  { return joinSubs("|", f.Subs) }
func (f *Not) String() string { return "(!" + f.Sub.String() + ")" }

func (f *Equal) String() string {
	return "(" + f.Attr + "=" + escapeValue(f.Value) + ")"
}
func (f *Present) String() string { return "(" + f.Attr + "=*)" }
func (f *GreaterOrEqual) String() string {
	return "(" + f.Attr + ">=" + escapeValue(f.Value) + ")"
}
func (f *LessOrEqual) String() string {
	return "(" + f.Attr + "<=" + escapeValue(f.Value) + ")"
}
func (f *Approx) String() string {
	return "(" + f.Attr + "~=" + escapeValue(f.Value) + ")"
}

func (f *Substrings) String() string {
	var b strings.Builder
	b.WriteString("(" + f.Attr + "=")
	b.WriteString(escapeValue(f.Initial))
	b.WriteString("*")
	for _, a := range f.Any {
		b.WriteString(escapeValue(a) + "*")
	}
	b.WriteString(escapeValue(f.Final) + ")")
	return b.String()
}

// escapeValue 는 값 안의 특수 글자를 \XX 로 바꾼다 (RFC 4515 §3).
//
// 이걸 빼먹으면 값에 괄호 하나만 넣어도 필터의 뜻이 통째로 바뀐다 — SQL
// 주입과 똑같은 사고가 LDAP 에도 있다. 7부에서 "사용자가 친 아이디를
// 필터에 그대로 넣지 말 것" 으로 다시 나온다.
func escapeValue(s string) string {
	var b strings.Builder
	for i := 0; i < len(s); i++ {
		switch c := s[i]; c {
		case '*', '(', ')', '\\', 0x00:
			fmt.Fprintf(&b, "\\%02x", c)
		default:
			b.WriteByte(c)
		}
	}
	return b.String()
}

// ── 필터: 나무 → 바이트 ──────────────────────────────────────────────

// 필터의 [n] 번호. RFC 4511 §4.5.1.7.
const (
	filterAnd             = 0
	filterOr              = 1
	filterNot             = 2
	filterEqualityMatch   = 3
	filterSubstrings      = 4
	filterGreaterOrEqual  = 5
	filterLessOrEqual     = 6
	filterPresent         = 7
	filterApproxMatch     = 8
	filterExtensibleMatch = 9
)

func attrValue(attr, value string) []byte {
	return concat([][]byte{ber.Str(attr), ber.Str(value)})
}

func EncodeFilter(f Filter) []byte {
	switch v := f.(type) {
	case *And:
		return ber.Encode(ber.Tag(ber.Context, true, filterAnd),
			encodeSubs(v.Subs))
	case *Or:
		return ber.Encode(ber.Tag(ber.Context, true, filterOr),
			encodeSubs(v.Subs))
	case *Not:
		return ber.Encode(ber.Tag(ber.Context, true, filterNot),
			EncodeFilter(v.Sub))
	case *Equal:
		return ber.Encode(
			ber.Tag(ber.Context, true, filterEqualityMatch),
			attrValue(v.Attr, v.Value))
	case *GreaterOrEqual:
		return ber.Encode(
			ber.Tag(ber.Context, true, filterGreaterOrEqual),
			attrValue(v.Attr, v.Value))
	case *LessOrEqual:
		return ber.Encode(ber.Tag(ber.Context, true, filterLessOrEqual),
			attrValue(v.Attr, v.Value))
	case *Approx:
		return ber.Encode(ber.Tag(ber.Context, true, filterApproxMatch),
			attrValue(v.Attr, v.Value))
	case *Present:
		// present 만 원시형이다 — 안에 TLV 가 없고 이름이 바로 온다.
		return ber.Encode(ber.Tag(ber.Context, false, filterPresent),
			[]byte(v.Attr))
	case *Substrings:
		return ber.Encode(ber.Tag(ber.Context, true, filterSubstrings),
			concat([][]byte{ber.Str(v.Attr), encodeSubstrings(v)}))
	}
	panic(fmt.Sprintf("모르는 필터 %T", f))
}

func encodeSubs(subs []Filter) []byte {
	var out []byte
	for _, s := range subs {
		out = append(out, EncodeFilter(s)...)
	}
	return out
}

// 부분 문자열의 조각도 [0] initial · [1] any · [2] final 로 번호가
// 붙는다.
func encodeSubstrings(v *Substrings) []byte {
	var parts [][]byte
	if v.Initial != "" {
		parts = append(parts,
			ber.Encode(ber.Tag(ber.Context, false, 0),
				[]byte(v.Initial)))
	}
	for _, a := range v.Any {
		parts = append(parts,
			ber.Encode(ber.Tag(ber.Context, false, 1), []byte(a)))
	}
	if v.Final != "" {
		parts = append(parts,
			ber.Encode(ber.Tag(ber.Context, false, 2), []byte(v.Final)))
	}
	return ber.Seq(parts...)
}

// ── 필터: 바이트 → 나무 ──────────────────────────────────────────────

func ParseFilter(t ber.TLV) (Filter, error) {
	switch t.Num() {
	case filterAnd, filterOr:
		kids, err := ber.Children(t.Value)
		if err != nil {
			return nil, err
		}
		if len(kids) == 0 {
			return nil, errors.New("&/| 안이 비어 있다")
		}
		subs := make([]Filter, 0, len(kids))
		for _, k := range kids {
			s, err := ParseFilter(k)
			if err != nil {
				return nil, err
			}
			subs = append(subs, s)
		}
		if t.Num() == filterAnd {
			return &And{Subs: subs}, nil
		}
		return &Or{Subs: subs}, nil

	case filterNot:
		inner, _, err := ber.Next(t.Value)
		if err != nil {
			return nil, err
		}
		s, err := ParseFilter(inner)
		if err != nil {
			return nil, err
		}
		return &Not{Sub: s}, nil

	case filterEqualityMatch, filterGreaterOrEqual,
		filterLessOrEqual, filterApproxMatch:
		kids, err := ber.Children(t.Value)
		if err != nil || len(kids) != 2 {
			return nil, errors.New("비교 필터는 이름과 값 둘이다")
		}
		attr, val := kids[0].Str(), kids[1].Str()
		switch t.Num() {
		case filterEqualityMatch:
			return &Equal{Attr: attr, Value: val}, nil
		case filterGreaterOrEqual:
			return &GreaterOrEqual{Attr: attr, Value: val}, nil
		case filterLessOrEqual:
			return &LessOrEqual{Attr: attr, Value: val}, nil
		}
		return &Approx{Attr: attr, Value: val}, nil

	case filterPresent:
		return &Present{Attr: string(t.Value)}, nil

	case filterSubstrings:
		return parseSubstrings(t)
	}
	return nil, fmt.Errorf("모르는 필터 종류 [%d]", t.Num())
}

func parseSubstrings(t ber.TLV) (Filter, error) {
	kids, err := ber.Children(t.Value)
	if err != nil || len(kids) != 2 {
		return nil, errors.New("부분 문자열 필터의 칸이 모자란다")
	}
	out := &Substrings{Attr: kids[0].Str()}
	pieces, err := ber.Children(kids[1].Value)
	if err != nil {
		return nil, err
	}
	if len(pieces) == 0 {
		return nil, errors.New("부분 문자열에 조각이 없다")
	}
	for _, p := range pieces {
		switch p.Num() {
		case 0:
			out.Initial = string(p.Value)
		case 1:
			out.Any = append(out.Any, string(p.Value))
		case 2:
			out.Final = string(p.Value)
		default:
			return nil, fmt.Errorf("모르는 조각 [%d]", p.Num())
		}
	}
	return out, nil
}

// ── 필터: 글 → 나무 ──────────────────────────────────────────────────

// ParseFilterString 은 사람이 쓴 (&(a=1)(b=2)) 를 나무로 만든다.
//
// 재귀 하강 방식이다. 괄호가 균형을 이루는지, 안이 비지 않았는지 등
// 규칙을 그대로 코드에 적었다. O(글자 수).
func ParseFilterString(s string) (Filter, error) {
	p := &fparser{s: s}
	f, err := p.filter()
	if err != nil {
		return nil, err
	}
	if p.i != len(p.s) {
		return nil, fmt.Errorf("%d번째 글자 뒤에 남은 것이 있다", p.i)
	}
	return f, nil
}

type fparser struct {
	s string
	i int
}

func (p *fparser) filter() (Filter, error) {
	if p.i >= len(p.s) || p.s[p.i] != '(' {
		return nil, errors.New("필터는 ( 로 시작해야 한다")
	}
	p.i++ // (
	if p.i >= len(p.s) {
		return nil, errors.New("필터가 갑자기 끝났다")
	}
	var f Filter
	var err error
	switch p.s[p.i] {
	case '&', '|':
		op := p.s[p.i]
		p.i++
		var subs []Filter
		for p.i < len(p.s) && p.s[p.i] == '(' {
			sub, e := p.filter()
			if e != nil {
				return nil, e
			}
			subs = append(subs, sub)
		}
		if len(subs) == 0 {
			return nil, errors.New("&/| 안에 조건이 없다")
		}
		if op == '&' {
			f = &And{Subs: subs}
		} else {
			f = &Or{Subs: subs}
		}
	case '!':
		p.i++
		sub, e := p.filter()
		if e != nil {
			return nil, e
		}
		f = &Not{Sub: sub}
		if p.i < len(p.s) && p.s[p.i] == '(' {
			return nil, errors.New("! 안에는 조건이 하나만 온다")
		}
	default:
		f, err = p.simple()
		if err != nil {
			return nil, err
		}
	}
	if p.i >= len(p.s) || p.s[p.i] != ')' {
		return nil, errors.New("닫는 ) 가 없다")
	}
	p.i++ // )
	return f, nil
}

// simple 은 (이름 연산자 값) 하나를 읽는다.
func (p *fparser) simple() (Filter, error) {
	start := p.i
	const stops = "=<>~)"
	for p.i < len(p.s) && !strings.ContainsRune(stops, rune(p.s[p.i])) {
		p.i++
	}
	attr := p.s[start:p.i]
	if attr == "" {
		return nil, errors.New("속성 이름이 없다")
	}
	if p.i >= len(p.s) {
		return nil, errors.New("연산자가 없다")
	}
	op := "="
	switch p.s[p.i] {
	case '>', '<', '~':
		if p.i+1 >= len(p.s) || p.s[p.i+1] != '=' {
			return nil, fmt.Errorf("%c 뒤에는 = 가 와야 한다", p.s[p.i])
		}
		op = p.s[p.i : p.i+2]
		p.i += 2
	case '=':
		p.i++
	default:
		return nil, errors.New("연산자가 없다")
	}
	vs := p.i
	for p.i < len(p.s) && p.s[p.i] != ')' {
		p.i++
	}
	raw := p.s[vs:p.i]

	switch op {
	case ">=":
		v, err := unescapeValue(raw)
		return &GreaterOrEqual{Attr: attr, Value: v}, err
	case "<=":
		v, err := unescapeValue(raw)
		return &LessOrEqual{Attr: attr, Value: v}, err
	case "~=":
		v, err := unescapeValue(raw)
		return &Approx{Attr: attr, Value: v}, err
	}
	// = 는 별표가 있느냐로 갈린다.
	if raw == "*" {
		return &Present{Attr: attr}, nil
	}
	if strings.Contains(raw, "*") {
		return parseSubstringValue(attr, raw)
	}
	v, err := unescapeValue(raw)
	return &Equal{Attr: attr, Value: v}, err
}

func parseSubstringValue(attr, raw string) (Filter, error) {
	parts := strings.Split(raw, "*")
	out := &Substrings{Attr: attr}
	for i, part := range parts {
		v, err := unescapeValue(part)
		if err != nil {
			return nil, err
		}
		switch {
		case i == 0:
			out.Initial = v
		case i == len(parts)-1:
			out.Final = v
		case v != "":
			out.Any = append(out.Any, v)
		}
	}
	return out, nil
}

// unescapeValue 는 \XX 를 원래 바이트로 되돌린다.
func unescapeValue(s string) (string, error) {
	if !strings.Contains(s, "\\") {
		return s, nil
	}
	var b strings.Builder
	for i := 0; i < len(s); i++ {
		if s[i] != '\\' {
			b.WriteByte(s[i])
			continue
		}
		if i+2 >= len(s) {
			return "", errors.New("\\ 뒤에 16진수 두 자리가 없다")
		}
		var v byte
		for _, c := range []byte{s[i+1], s[i+2]} {
			switch {
			case c >= '0' && c <= '9':
				v = v<<4 | (c - '0')
			case c >= 'a' && c <= 'f':
				v = v<<4 | (c - 'a' + 10)
			case c >= 'A' && c <= 'F':
				v = v<<4 | (c - 'A' + 10)
			default:
				return "", fmt.Errorf("\\ 뒤 %q 는 16진수가 아니다", c)
			}
		}
		b.WriteByte(v)
		i += 2
	}
	return b.String(), nil
}
