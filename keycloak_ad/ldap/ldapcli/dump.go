// dump.go — 오간 바이트를 사람이 읽는 나무로 풀어 준다.
//
// 3부의 핵심 도구다. "LDAP 은 바이트다" 를 글로 백 번 말하는 것보다,
// 진짜로 나간 바이트 옆에 그 뜻을 나란히 적어 주는 편이 낫다.
//
//	30 0C                    SEQUENCE (12바이트)        LDAPMessage
//	  02 01 01               INTEGER 1                  messageID
//	  60 07                  [APPLICATION 0] (7바이트)   BindRequest
//	    02 01 03             INTEGER 3                  version
//	    04 00 ""             OCTET STRING               name
//	    80 00                [0] (0바이트)               simple 비밀번호
package main

import (
	"fmt"
	"strings"
	"unicode/utf8"

	"treasure/keycloak_ad/ldap/ber"
	"treasure/keycloak_ad/ldap/proto"
)

// LDAP 이 [APPLICATION n] 에 붙인 이름들.
var appNames = map[int]string{
	proto.OpBindRequest:       "BindRequest",
	proto.OpBindResponse:      "BindResponse",
	proto.OpUnbindRequest:     "UnbindRequest",
	proto.OpSearchRequest:     "SearchRequest",
	proto.OpSearchResultEntry: "SearchResultEntry",
	proto.OpSearchResultDone:  "SearchResultDone",
	proto.OpModifyRequest:     "ModifyRequest",
	proto.OpAddRequest:        "AddRequest",
	proto.OpDelRequest:        "DelRequest",
	proto.OpExtendedRequest:   "ExtendedRequest",
	proto.OpExtendedResponse:  "ExtendedResponse",
}

// 각 연산 안에서 칸마다 붙는 이름. 순서가 곧 뜻이다 — LDAP 의
// 메시지에는 칸 이름이 실려 가지 않고, 몇 번째냐로만 구별한다.
var fieldNames = map[int][]string{
	proto.OpBindRequest: {"version", "name", "authentication"},
	proto.OpBindResponse: {"resultCode", "matchedDN",
		"diagnosticMessage"},
	proto.OpSearchRequest: {"baseObject", "scope", "derefAliases",
		"sizeLimit", "timeLimit", "typesOnly", "filter", "attributes"},
	proto.OpSearchResultEntry: {"objectName", "attributes"},
	proto.OpSearchResultDone: {"resultCode", "matchedDN",
		"diagnosticMessage"},
}

// Dump 는 메시지 한 통을 나무로 풀어 준다. 못 읽는 자리가 나오면 거기서
// 멈추되, 읽은 데까지는 보여 준다 — 어디서 어긋났는지가 곧 단서다.
func Dump(b []byte) string {
	var sb strings.Builder
	dumpNode(&sb, b, 0, "LDAPMessage", -1, 0)
	return sb.String()
}

// dumpNode 는 TLV 하나를 찍고, 묶음이면 안으로 들어간다.
//
//	op    지금 어느 연산 안인가 (-1 이면 아직 모른다)
//	idx   그 연산 안에서 몇 번째 칸인가
func dumpNode(sb *strings.Builder, b []byte, depth int, note string,
	op, idx int) {
	tlv, rest, err := ber.Next(b)
	if err != nil {
		fmt.Fprintf(sb, "%s(읽을 수 없는 바이트 %d개: %v)\n",
			indent(depth), len(b), err)
		return
	}

	head := len(b) - len(rest) - len(tlv.Value) // 태그 + 길이 바이트 수
	// 묶음은 머리만, 값은 머리와 내용을 함께 보여 준다. 묶음의 내용은
	// 어차피 바로 아래 줄들에 다시 나오므로 두 번 찍을 이유가 없다.
	shownBytes := b[:head]
	if !tlv.Constructed() {
		shownBytes = b[:head+len(tlv.Value)]
	}
	line := indent(depth) + hexOf(shownBytes)
	kind, shown := describeTLV(tlv, op)
	fmt.Fprintf(sb, "%-38s %-30s %s\n", line, kind+shown, note)

	if tlv.Constructed() {
		s, nextOp := childNames(tlv, op, depth)
		inner := tlv.Value
		i := 0
		for len(inner) > 0 {
			name := ""
			if i < len(s) {
				name = s[i]
			}
			before := len(inner)
			dumpChild(sb, inner, depth+1, name, nextOp, i)
			consumed := consumedBy(inner)
			if consumed <= 0 || consumed > before {
				break
			}
			inner = inner[consumed:]
			i++
		}
	}
	// 형제가 남아 있어도 여기서는 찍지 않는다 — 부르는 쪽이 이어서
	// 돈다.
}

func dumpChild(sb *strings.Builder, b []byte, depth int, note string,
	op, idx int) {
	// 필터 자리는 바이트 대신 사람이 읽는 글을 함께 보여 준다.
	if op == proto.OpSearchRequest && idx == 6 {
		if tlv, _, err := ber.Next(b); err == nil {
			if f, ferr := proto.ParseFilter(tlv); ferr == nil {
				head := len(b) - len(tlv.Value)
				if head > len(b) {
					head = len(b)
				}
				fmt.Fprintf(sb, "%-38s %-30s %s\n",
					indent(depth)+hexOf(b[:head]),
					"필터", note+" = "+f.String())
				return
			}
		}
	}
	dumpNode(sb, b, depth, note, op, idx)
}

// consumedBy 는 앞에서 TLV 하나가 몇 바이트를 먹는지 센다.
func consumedBy(b []byte) int {
	n, err := ber.MessageLength(b)
	if err != nil {
		return -1
	}
	return n
}

// childNames 는 이 묶음의 자식들에게 붙일 이름과, 안쪽에서 이어질 연산
// 번호.
func childNames(t ber.TLV, op, depth int) ([]string, int) {
	if t.Class() == ber.Application {
		if names, ok := fieldNames[t.Num()]; ok {
			return names, t.Num()
		}
		return nil, t.Num()
	}
	// 가장 바깥 SEQUENCE 만 LDAPMessage 다. depth 를 안 보면 안쪽의
	// 아무 SEQUENCE 나 messageID 라는 이름표를 달게 된다.
	if t.Tag == ber.TagSequence && depth == 0 {
		return []string{"messageID", "protocolOp", "controls"}, -1
	}
	return nil, op
}

// describeTLV 는 태그 한 바이트를 사람 말로 옮기고, 값도 짧게 보여
// 준다.
func describeTLV(t ber.TLV, op int) (kind, shown string) {
	switch t.Class() {
	case ber.Application:
		name := appNames[t.Num()]
		if name == "" {
			name = fmt.Sprintf("[APPLICATION %d]", t.Num())
		}
		return name, fmt.Sprintf(" (%d바이트)", len(t.Value))
	case ber.Context:
		// 바인드 안의 [0] 은 simple 비밀번호다.
		bindSimple := op == proto.OpBindRequest && t.Num() == 0
		if bindSimple && !t.Constructed() {
			return "[0] simple 비밀번호", ""
		}
		return fmt.Sprintf("[%d]", t.Num()),
			fmt.Sprintf(" (%d바이트)", len(t.Value))
	}
	switch t.Tag {
	case ber.TagSequence:
		return "SEQUENCE", fmt.Sprintf(" (%d바이트)", len(t.Value))
	case ber.TagSet:
		return "SET", fmt.Sprintf(" (%d바이트)", len(t.Value))
	case ber.TagInteger:
		n, _ := t.Int()
		return "INTEGER", fmt.Sprintf(" %d", n)
	case ber.TagEnumerated:
		n, _ := t.Int()
		return "ENUMERATED", fmt.Sprintf(" %d", n)
	case ber.TagBoolean:
		v, _ := t.Bool()
		return "BOOLEAN", fmt.Sprintf(" %v", v)
	case ber.TagOctetString:
		return "OCTET STRING", " " + showValue(t.Value)
	}
	return fmt.Sprintf("태그 0x%02X", t.Tag),
		fmt.Sprintf(" (%d바이트)", len(t.Value))
}

// showValue 는 값을 글자로 보여 줄지 16진수로 보여 줄지 고른다.
//
// objectGUID 처럼 글자가 아닌 값을 따옴표로 감싸 찍으면, 읽는 사람이
// "저건 글자구나" 로 잘못 배운다. 그 오해가 7부에서 진짜 사고가 된다.
func showValue(v []byte) string {
	if len(v) == 0 {
		return `""`
	}
	if isText(v) {
		s := string(v)
		if len(s) > 34 {
			s = s[:31] + "…"
		}
		return fmt.Sprintf("%q", s)
	}
	return hexOf(v)
}

func isText(v []byte) bool {
	if !utf8.Valid(v) {
		return false
	}
	for _, c := range v {
		if c < 0x20 && c != '\t' {
			return false
		}
	}
	return true
}

func hexOf(b []byte) string {
	var parts []string
	for i, c := range b {
		if i == 8 {
			parts = append(parts, "…")
			break
		}
		parts = append(parts, fmt.Sprintf("%02X", c))
	}
	return strings.Join(parts, " ")
}

func indent(n int) string { return strings.Repeat("  ", n) }

// cells 는 화면 칸 수다. 한글·CJK 는 두 칸이라 글자 수로 세면
// 안 맞는다. tools/width.py · tools/embed_mono_font.py 와 같은 규칙.
func cells(s string) int {
	n := 0
	for _, r := range s {
		if isWide(r) {
			n += 2
		} else {
			n++
		}
	}
	return n
}

func isWide(r rune) bool {
	switch {
	case r >= 0x1100 && r <= 0x115F, // 한글 자모
		r >= 0x2E80 && r <= 0x303E, // CJK 부수·구두점
		r >= 0x3041 && r <= 0x33FF, // 가나·한글 호환·기호
		r >= 0x3400 && r <= 0x4DBF, // CJK 확장 A
		r >= 0x4E00 && r <= 0x9FFF, // CJK 기본
		r >= 0xAC00 && r <= 0xD7A3, // 한글 음절
		r >= 0xF900 && r <= 0xFAFF, // CJK 호환
		r >= 0xFF00 && r <= 0xFF60: // 전각 라틴
		return true
	}
	return false
}

// wrapCells 는 긴 글을 limit 칸 안으로 접는다. 어절 사이에서만 끊는다.
func wrapCells(s, pad string, limit int) []string {
	var out []string
	cur := ""
	for _, w := range strings.Fields(s) {
		cand := w
		if cur != "" {
			cand = cur + " " + w
		}
		if cells(pad+cand) > limit && cur != "" {
			out = append(out, pad+cur)
			cur = w
			continue
		}
		cur = cand
	}
	if cur != "" {
		out = append(out, pad+cur)
	}
	return out
}

// ── 답을 사람 말로 ───────────────────────────────────────────────────

// Describe 는 받은 응답을 한눈에 읽히게 적는다.
func Describe(m proto.Message) string {
	name := appNames[m.OpNum()]
	if name == "" {
		name = fmt.Sprintf("[APPLICATION %d]", m.OpNum())
	}
	var sb strings.Builder
	fmt.Fprintf(&sb, "#%d %s\n", m.ID, name)

	kids, err := ber.Children(m.Op.Value)
	if err != nil {
		fmt.Fprintf(&sb, "  (풀 수 없다: %v)\n", err)
		return sb.String()
	}

	switch m.OpNum() {
	case proto.OpSearchResultEntry:
		return describeEntry(&sb, kids)
	case proto.OpBindResponse, proto.OpSearchResultDone:
		if len(kids) < 3 {
			return sb.String()
		}
		code, _ := kids[0].Int()
		fmt.Fprintf(&sb, "  결과: %s (%d)\n",
			proto.ResultName(int(code)), code)
		if d := kids[2].Str(); d != "" {
			// AD 의 진단 문구는 한 줄이 120칸을 넘는다. 값은 그대로
			// 두고 보여 줄 때만 접는다 — 옆으로 밀리면 정작 봐야 할
			// "data XXX" 가 안 보인다.
			lines := wrapCells("진단: "+d, "  ", 72)
			for i, l := range lines {
				if i > 0 {
					l = "        " + strings.TrimSpace(l)
				}
				fmt.Fprintln(&sb, l)
			}
			if why := ExplainADCode(d); why != "" {
				for _, l := range wrapCells("→ "+why, "        ", 72) {
					fmt.Fprintln(&sb, l)
				}
			}
		}
	}
	return sb.String()
}

func describeEntry(sb *strings.Builder, kids []ber.TLV) string {
	if len(kids) < 2 {
		return sb.String()
	}
	fmt.Fprintf(sb, "  dn: %s\n", kids[0].Str())
	attrs, err := ber.Children(kids[1].Value)
	if err != nil {
		return sb.String()
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
		for _, v := range vals {
			fmt.Fprintf(sb, "  %s: %s\n",
				one[0].Str(), plainValue(v.Value))
		}
	}
	return sb.String()
}

func plainValue(v []byte) string {
	if isText(v) {
		return string(v)
	}
	return fmt.Sprintf("<%d바이트 이진값> %s", len(v), hexOf(v))
}

// ExplainADCode 는 AD 의 진단 문구에서 "data XXX" 를 찾아 뜻을 붙인다.
//
// AD 는 실패 이유를 결과 코드로 알려 주지 않는다 — 전부 49 다. 이유는
// 이 문구 끝에 숨어 있고, 그 숫자를 읽을 줄 아는 것이 7부 진단의
// 절반이다.
func ExplainADCode(diag string) string {
	meanings := map[string]string{
		"525": "그런 계정이 없다 (아이디를 다시 볼 것)",
		"52e": "비밀번호가 틀렸다 (계정은 있다)",
		"530": "지금 시간에는 로그인할 수 없다",
		"531": "이 컴퓨터에서는 로그인할 수 없다",
		"532": "비밀번호 기간이 지났다",
		"533": "계정이 꺼져 있다 (비밀번호는 맞아도 못 들어온다)",
		"701": "계정 기간이 지났다",
		"773": "비밀번호를 반드시 바꿔야 한다",
		"775": "계정이 잠겼다 (여러 번 틀렸다)",
	}
	i := strings.Index(diag, "data ")
	if i < 0 {
		return ""
	}
	rest := diag[i+len("data "):]
	end := strings.IndexAny(rest, ", ")
	if end < 0 {
		end = len(rest)
	}
	code := strings.TrimSpace(rest[:end])
	if why, ok := meanings[code]; ok {
		return fmt.Sprintf("data %s — %s", code, why)
	}
	return ""
}
