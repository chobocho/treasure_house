package main

import (
	"strings"
	"testing"

	"treasure/keycloak_ad/ldap/ber"
	"treasure/keycloak_ad/ldap/proto"
)

func TestDumpAnonymousBind(t *testing.T) {
	raw := ber.Seq(ber.Int(1),
		ber.Encode(ber.Tag(ber.Application, true, proto.OpBindRequest),
			join(ber.Int(3), ber.Str(""),
				ber.Encode(ber.Tag(ber.Context, false, 0), nil))))
	got := Dump(raw)

	for _, want := range []string{
		"30 0C", "SEQUENCE", "LDAPMessage",
		"02 01 01", "INTEGER 1", "messageID",
		"60 07", "BindRequest",
		"INTEGER 3", "version",
		"simple",
	} {
		if !strings.Contains(got, want) {
			t.Errorf("풀이에 %q 가 없다:\n%s", want, got)
		}
	}
}

// 안쪽으로 들어갈수록 들여쓰기가 깊어져야 한다 — 나무 모양이 보여야
// 한다.
//
// 묶음 셋을 겹쳐 두면 깊이가 0·1·2·3 네 단계로 나와야 한다.
// (형제끼리는 같은 깊이이므로 "줄마다 깊어진다" 로 보면 안 된다.)
func TestDumpIndentsNesting(t *testing.T) {
	raw := ber.Seq(ber.Int(1), ber.Seq(ber.Seq(ber.Int(2))))
	lines := strings.Split(strings.TrimRight(Dump(raw), "\n"), "\n")
	depth := func(s string) int {
		return (len(s) - len(strings.TrimLeft(s, " "))) / 2
	}
	if len(lines) != 5 {
		t.Fatalf("줄이 %d개다:\n%s", len(lines),
			strings.Join(lines, "\n"))
	}
	want := []int{0, 1, 1, 2, 3}
	for i, w := range want {
		if got := depth(lines[i]); got != w {
			t.Errorf("%d번째 줄 깊이 %d, 원하는 것 %d:\n%s",
				i, got, w, strings.Join(lines, "\n"))
		}
	}
}

func TestDumpShowsStringsAndBytes(t *testing.T) {
	got := Dump(ber.Seq(ber.Str("minji")))
	if !strings.Contains(got, `"minji"`) {
		t.Errorf("글자를 안 보여 준다:\n%s", got)
	}
	// 글자로 볼 수 없는 값은 16진수로 보여 준다 — objectGUID 가 그렇다.
	guid := []byte{0x98, 0xD3, 0x08, 0x98, 0x00, 0x8B, 0xDC, 0x12,
		0x27, 0x95, 0xB5, 0x5F, 0x90, 0xA0, 0xAA, 0x29}
	got = Dump(ber.Seq(ber.Bytes(guid)))
	if strings.Contains(got, `"`) {
		t.Errorf("이진값을 글자처럼 보여 준다:\n%s", got)
	}
	if !strings.Contains(got, "98 D3") {
		t.Errorf("16진수가 없다:\n%s", got)
	}
}

// 필터는 바이트 나열이 아니라 사람이 읽는 글로도 함께 보여 준다.
func TestDumpSearchShowsFilterText(t *testing.T) {
	f, _ := proto.ParseFilterString("(&(objectClass=user)(cn=minji))")
	raw := ber.Seq(ber.Int(2),
		ber.Encode(
			ber.Tag(ber.Application, true, proto.OpSearchRequest),
			join(ber.Str("DC=ad"), ber.Enum(2), ber.Enum(0),
				ber.Int(0), ber.Int(0), ber.Bool(false),
				proto.EncodeFilter(f), ber.Seq(ber.Str("cn")))))
	got := Dump(raw)
	for _, want := range []string{
		"SearchRequest", "baseObject", "scope", "filter",
		"(&(objectClass=user)(cn=minji))",
	} {
		if !strings.Contains(got, want) {
			t.Errorf("%q 가 없다:\n%s", want, got)
		}
	}
}

// 못 읽는 바이트를 줘도 죽지 않고 "여기까지 읽었다" 를 보여 줘야 한다.
func TestDumpSurvivesGarbage(t *testing.T) {
	got := Dump([]byte{0x30, 0x05, 0x02, 0x01})
	if got == "" {
		t.Error("아무것도 안 보여 준다")
	}
	if !strings.Contains(got, "읽을 수 없") {
		t.Errorf("못 읽었다는 말이 없다:\n%s", got)
	}
}

func TestDescribeResult(t *testing.T) {
	raw := proto.BindResponse(9, proto.ResultInvalidCredentials, "",
		"80090308: LdapErr: DSID-0C09042F, data 52e, v4563")
	msg, err := proto.ParseMessage(raw)
	if err != nil {
		t.Fatal(err)
	}
	got := Describe(msg)
	for _, want := range []string{"BindResponse", "invalidCredentials",
		"data 52e"} {
		if !strings.Contains(got, want) {
			t.Errorf("%q 가 없다:\n%s", want, got)
		}
	}
}

func TestDescribeSearchEntry(t *testing.T) {
	raw := proto.SearchResultEntry(3, "CN=Kim Minji,OU=Students,DC=ad",
		[]proto.Attribute{
			{Name: "cn", Values: [][]byte{[]byte("Kim Minji")}},
			{Name: "objectGUID",
				Values: [][]byte{{0x98, 0xD3, 0x00, 0x01}}},
		})
	msg, _ := proto.ParseMessage(raw)
	got := Describe(msg)
	for _, want := range []string{"CN=Kim Minji", "cn: Kim Minji",
		"objectGUID"} {
		if !strings.Contains(got, want) {
			t.Errorf("%q 가 없다:\n%s", want, got)
		}
	}
	// 이진값은 글자로 우기지 않는다.
	if strings.Contains(got, "objectGUID: \x98") {
		t.Errorf("이진값을 그대로 찍었다:\n%s", got)
	}
}

// AD 의 진단 문구에서 "data XXX" 를 뽑아 뜻을 붙여 준다 —
// 이 한 줄이 7부 진단의 출발점이다.
func TestExplainADCode(t *testing.T) {
	cases := map[string]string{
		"…, data 52e, v4563": "비밀번호",
		"…, data 533, v4563": "꺼져",
		"…, data 775, v4563": "잠",
		"…, data 525, v4563": "계정",
		"그냥 오류":              "",
	}
	for diag, want := range cases {
		got := ExplainADCode(diag)
		if want == "" {
			if got != "" {
				t.Errorf("%q → %q, 빈 것이어야 한다", diag, got)
			}
			continue
		}
		if !strings.Contains(got, want) {
			t.Errorf("%q → %q, %q 가 있어야 한다", diag, got, want)
		}
	}
}

func join(parts ...[]byte) []byte {
	var out []byte
	for _, p := range parts {
		out = append(out, p...)
	}
	return out
}
