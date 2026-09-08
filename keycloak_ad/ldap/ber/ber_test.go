package ber

import (
	"bytes"
	"encoding/hex"
	"strings"
	"testing"
)

func hx(t *testing.T, s string) []byte {
	t.Helper()
	b, err := hex.DecodeString(strings.ReplaceAll(s, " ", ""))
	if err != nil {
		t.Fatalf("시험 벡터가 잘못됐다: %v", err)
	}
	return b
}

// 정수는 2의 보수 · 빅엔디언 · **가장 짧게** 적는다.
// 128 이 두 바이트가 되는 것이 요점이다 — 앞에 0x00 을 붙이지 않으면
// 음수(-128)로 읽히기 때문이다.
func TestIntGolden(t *testing.T) {
	cases := []struct {
		n   int64
		hex string
	}{
		{0, "02 01 00"},
		{1, "02 01 01"},
		{127, "02 01 7F"},
		{128, "02 02 00 80"},
		{255, "02 02 00 FF"},
		{256, "02 02 01 00"},
		{-1, "02 01 FF"},
		{-128, "02 01 80"},
		{-129, "02 02 FF 7F"},
		{32767, "02 02 7F FF"},
		{32768, "02 03 00 80 00"},
	}
	for _, c := range cases {
		got := Int(c.n)
		if !bytes.Equal(got, hx(t, c.hex)) {
			t.Errorf("Int(%d) = % X, 원하는 것 %s", c.n, got, c.hex)
		}
	}
}

func TestIntRoundTrip(t *testing.T) {
	for _, n := range []int64{0, 1, -1, 127, 128, -128, -129,
		32767, 32768, 1 << 40, -(1 << 40)} {
		tlv, rest, err := Next(Int(n))
		if err != nil || len(rest) != 0 {
			t.Fatalf("%d: %v · 남은 %d바이트", n, err, len(rest))
		}
		got, err := tlv.Int()
		if err != nil || got != n {
			t.Errorf("%d → %d (%v)", n, got, err)
		}
	}
}

// 길이는 127 까지 한 바이트, 그 위는 "길이의 길이" 를 앞에 붙인다.
func TestLengthGolden(t *testing.T) {
	cases := []struct {
		n   int
		hex string
	}{
		{0, "00"},
		{1, "01"},
		{127, "7F"},
		{128, "81 80"},
		{255, "81 FF"},
		{256, "82 01 00"},
		{65535, "82 FF FF"},
		{65536, "83 01 00 00"},
	}
	for _, c := range cases {
		got := EncodeLength(c.n)
		if !bytes.Equal(got, hx(t, c.hex)) {
			t.Errorf("EncodeLength(%d) = % X, 원하는 것 %s",
				c.n, got, c.hex)
		}
	}
}

// 진짜 LDAP 바이트. 익명 바인드 요청은 이 14바이트로 널리 알려져 있다.
//
//	LDAPMessage ::= SEQUENCE {
//	  messageID    INTEGER (1),
//	  protocolOp   [APPLICATION 0] SEQUENCE {   -- BindRequest
//	    version    INTEGER (3),
//	    name       LDAPDN ("")
//	    auth       [0] OCTET STRING ("") }}
func TestAnonymousBindGolden(t *testing.T) {
	want := hx(t, "30 0C 02 01 01 60 07 02 01 03 04 00 80 00")
	got := Seq(
		Int(1),
		Encode(Tag(Application, true, 0),
			join(Int(3), Str(""), Encode(Tag(Context, false, 0), nil))),
	)
	if !bytes.Equal(got, want) {
		t.Errorf("익명 바인드 = % X\n원하는 것          % X", got, want)
	}
}

func join(parts ...[]byte) []byte {
	var out []byte
	for _, p := range parts {
		out = append(out, p...)
	}
	return out
}

func TestTagBits(t *testing.T) {
	cases := []struct {
		class       Class
		constructed bool
		num         int
		want        byte
	}{
		{Universal, false, 2, 0x02},   // INTEGER
		{Universal, false, 4, 0x04},   // OCTET STRING
		{Universal, true, 16, 0x30},   // SEQUENCE
		{Universal, true, 17, 0x31},   // SET
		{Universal, false, 10, 0x0A},  // ENUMERATED
		{Application, true, 0, 0x60},  // BindRequest
		{Application, true, 1, 0x61},  // BindResponse
		{Application, false, 2, 0x42}, // UnbindRequest (원시형이다)
		{Application, true, 3, 0x63},  // SearchRequest
		{Application, true, 4, 0x64},  // SearchResultEntry
		{Application, true, 5, 0x65},  // SearchResultDone
		{Context, true, 0, 0xA0},      // and 필터 · 그리고 컨트롤
		{Context, true, 3, 0xA3},      // equalityMatch 필터
		{Context, false, 7, 0x87},     // present 필터 (원시형이다)
		{Context, false, 0, 0x80},     // simple 인증
	}
	for _, c := range cases {
		if got := Tag(c.class, c.constructed, c.num); got != c.want {
			t.Errorf("Tag(%d,%v,%d) = %02X, 원하는 것 %02X",
				c.class, c.constructed, c.num, got, c.want)
		}
	}
}

// 태그 번호가 30 을 넘으면 여러 바이트로 적어야 한다. 우리는 그걸
// 만들지 않는다 — LDAP 은 24 까지만 쓴다. 조용히 틀린 바이트를 내는
// 대신 죽는다.
func TestTagTooBigPanics(t *testing.T) {
	defer func() {
		if recover() == nil {
			t.Error("태그 번호 31 인데 안 죽었다")
		}
	}()
	Tag(Application, true, 31)
}

func TestChildren(t *testing.T) {
	msg := Seq(Int(7), Str("minji"), Bool(true))
	tlv, _, err := Next(msg)
	if err != nil {
		t.Fatal(err)
	}
	kids, err := Children(tlv.Value)
	if err != nil {
		t.Fatal(err)
	}
	if len(kids) != 3 {
		t.Fatalf("자식 %d개, 원하는 것 3", len(kids))
	}
	if n, _ := kids[0].Int(); n != 7 {
		t.Errorf("첫째 = %d", n)
	}
	if kids[1].Str() != "minji" {
		t.Errorf("둘째 = %q", kids[1].Str())
	}
	if v, _ := kids[2].Bool(); !v {
		t.Error("셋째가 참이 아니다")
	}
}

// 옥텟 문자열은 글자가 아니라 바이트다. objectGUID 는 16바이트
// 이진값이고, 그 안에 0x00 이 들어 있어도 그대로 실려야 한다 — 7부의
// 핵심이다.
func TestOctetStringKeepsRawBytes(t *testing.T) {
	raw := []byte{0x00, 0xFF, 0x10, 0x00, 0x7F}
	tlv, _, err := Next(Bytes(raw))
	if err != nil {
		t.Fatal(err)
	}
	if !bytes.Equal(tlv.Value, raw) {
		t.Errorf("% X 가 % X 로 바뀌었다", raw, tlv.Value)
	}
}

func TestNextRejectsMalformed(t *testing.T) {
	cases := []struct {
		name string
		hex  string
	}{
		{"빈 입력", ""},
		{"길이 바이트가 없다", "02"},
		{"내용이 모자란다", "02 03 01"},
		{"긴 길이의 바이트가 모자란다", "04 82 01"},
		{"길이가 남은 바이트보다 크다", "04 05 01 02"},
		// BER 에는 "끝날 때까지" 라는 부정 길이 형식이 있지만,
		// RFC 4511 §5.1 은 LDAP 에서 definite form 만 쓰라고 못 박았다.
		{"부정 길이 형식", "30 80 02 01 01 00 00"},
		{"길이 바이트가 너무 많다", "04 85 01 01 01 01 01"},
	}
	for _, c := range cases {
		if _, _, err := Next(hx(t, c.hex)); err == nil {
			t.Errorf("%s: 오류가 나야 한다 (%s)", c.name, c.hex)
		}
	}
}

func TestChildrenRejectsTrailingGarbage(t *testing.T) {
	if _, err := Children(hx(t, "02 01 01 04")); err == nil {
		t.Error("꼬리에 쓰레기가 붙었는데 통과했다")
	}
}

// 정수 자리에 빈 내용이 오면 오류다. 길이 0 인 INTEGER 는 뜻이 없다.
func TestIntRejectsEmpty(t *testing.T) {
	tlv := TLV{Tag: 0x02, Value: nil}
	if _, err := tlv.Int(); err == nil {
		t.Error("빈 INTEGER 가 통과했다")
	}
}

// 아홉 바이트짜리 정수는 int64 에 안 들어간다. 조용히 잘리면 안 된다.
func TestIntRejectsTooLong(t *testing.T) {
	tlv := TLV{Tag: 0x02, Value: make([]byte, 9)}
	if _, err := tlv.Int(); err == nil {
		t.Error("9바이트 정수가 통과했다")
	}
}

func TestNextReturnsRest(t *testing.T) {
	buf := append(Int(1), Str("뒤에 붙은 것")...)
	tlv, rest, err := Next(buf)
	if err != nil {
		t.Fatal(err)
	}
	if n, _ := tlv.Int(); n != 1 {
		t.Errorf("첫 값 = %d", n)
	}
	tlv2, rest2, err := Next(rest)
	if err != nil || len(rest2) != 0 {
		t.Fatalf("둘째: %v · 남은 %d", err, len(rest2))
	}
	if tlv2.Str() != "뒤에 붙은 것" {
		t.Errorf("둘째 값 = %q", tlv2.Str())
	}
}

// 메시지 하나가 여러 번에 나눠 도착하는 것은 TCP 에서 늘 있는 일이다.
// 얼마나 더 읽어야 하는지 알려 주는 함수가 서버의 읽기 고리에 꼭
// 필요하다.
func TestMessageLength(t *testing.T) {
	msg := Seq(Int(1), Str("minji"))
	for cut := 0; cut < len(msg); cut++ {
		n, err := MessageLength(msg[:cut])
		if cut < 2 {
			if err != ErrShort {
				t.Errorf("%d바이트: %v, ErrShort 여야 한다", cut, err)
			}
			continue
		}
		if err != nil {
			t.Fatalf("%d바이트: %v", cut, err)
		}
		if n != len(msg) {
			t.Errorf("%d바이트에서 전체 길이 %d, 원하는 것 %d",
				cut, n, len(msg))
		}
	}
	n, err := MessageLength(msg)
	if err != nil || n != len(msg) {
		t.Errorf("전체를 줬을 때 %d (%v)", n, err)
	}
}
