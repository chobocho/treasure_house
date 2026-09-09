// dir.go — 가짜 AD 가 들고 있는 "학적부" 그 자체.
//
// 여기가 하는 일은 셋이다.
//
//  1. LDIF 를 읽어 항목들을 만든다
//  2. 비밀번호를 맞춰 본다 (bind) — AD 의 실패 코드까지 흉내 낸다
//  3. 조건에 맞는 항목을 찾아 준다 (search)
//
// 진짜 AD 를 흉내 내되, Keycloak 이 실제로 쓰는 만큼만 한다. 안 하는
// 것은 server.go 머리말에 적어 두었다.
package fakead

import (
	"bufio"
	"encoding/base64"
	"fmt"
	"os"
	"strings"
	"sync"
	"time"

	"treasure/keycloak_ad/ldap/proto"
)

// AD 가 바인드 실패의 이유를 알려 주는 코드. 진단 문구 끝의 "data XXX"
// 다. AD 는 이유를 자세히 말해 주지 않는 대신 이 숫자를 남긴다 — 7부의
// 진단은 이 숫자를 읽는 데서 시작한다.
const (
	adNoSuchUser  = "525" // 그런 계정이 없다
	adBadPassword = "52e" // 비밀번호가 틀렸다
	adDisabled    = "533" // 계정이 꺼져 있다
	adExpired     = "532" // 비밀번호 기간이 지났다 (우리는 안 쓴다)
	adLocked      = "775" // 여러 번 틀려 잠겼다
)

// 잠금 정책. AD 의 기본값(창 안에서 다섯 번)을 흉내 냈다.
const (
	lockThreshold = 5
	lockWindow    = 10 * time.Minute
	lockDuration  = 30 * time.Minute
)

// userAccountControl 의 비트. 이 셋만 쓴다 (Microsoft Learn 참고).
const (
	uacAccountDisable     = 0x0002  // 2
	uacNormalAccount      = 0x0200  // 512
	uacDontExpirePassword = 0x10000 // 65536
)

// 검색으로 절대 내보내지 않는 칸. 진짜 AD 에는 이 칸 자체가 없다.
var neverReturn = map[string]bool{"demopassword": true}

// Entry 는 항목 하나다. 속성 이름은 소문자로 통일해 두고(LDAP 은 이름의
// 대소문자를 가리지 않는다), 값은 바이트로 둔다(objectGUID 때문에).
type Entry struct {
	DN    string
	Attrs map[string][][]byte
}

// First 는 속성의 첫 값을 글자로 준다. 없으면 빈 글자.
func (e *Entry) First(name string) string {
	v := e.Attrs[strings.ToLower(name)]
	if len(v) == 0 {
		return ""
	}
	return string(v[0])
}

type failState struct {
	count int
	first time.Time // 이 창이 시작된 때
	until time.Time // 잠김이 풀리는 때
}

type Dir struct {
	mu sync.Mutex
	// 읽은 순서 그대로 — 검색 결과 순서를 고정한다
	entries []*Entry
	byDN    map[string]*Entry   // 정규화한 DN → 항목
	byUPN   map[string]*Entry   // 소문자 UPN → 항목
	groups  map[string][]string // 정규화한 사람 DN → 그룹 DN 목록
	fails   map[string]*failState
	now     func() time.Time
}

// normDN 은 DN 을 견줄 수 있는 꼴로 바꾼다.
//
// LDAP 의 DN 은 대소문자를 가리지 않고, 쉼표 뒤의 빈칸도 뜻이 없다.
// 그래서 "CN=Kim Minji, OU=Students, DC=ad" 와 "cn=kim
// minji,ou=students,dc=ad" 는 같은 사람이다. 이 함수가 그 규칙이다.
// (진짜 DN 규칙은 RFC 4514 로 훨씬 복잡하다 — 이스케이프, 여러 값 RDN
// 따위. 우리 자료에는 그런 것이 없으므로 여기까지만 한다.)
func normDN(dn string) string {
	parts := strings.Split(dn, ",")
	for i, p := range parts {
		parts[i] = strings.ToLower(strings.TrimSpace(p))
	}
	return strings.Join(parts, ",")
}

// ── LDIF 읽기 ────────────────────────────────────────────────────────

// LoadLDIFFile 은 파일 하나를 읽어 디렉터리를 만든다.
func LoadLDIFFile(path string) (*Dir, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer f.Close()

	d := &Dir{
		byDN: map[string]*Entry{}, byUPN: map[string]*Entry{},
		groups: map[string][]string{}, fails: map[string]*failState{},
		now: time.Now,
	}
	var cur *Entry
	flush := func() {
		if cur != nil {
			d.add(cur)
			cur = nil
		}
	}

	sc := bufio.NewScanner(f)
	sc.Buffer(make([]byte, 0, 64*1024), 1024*1024)
	lineNo := 0
	var pending string
	emit := func() error {
		if pending == "" {
			return nil
		}
		name, val, err := parseLDIFLine(pending)
		pending = ""
		if err != nil {
			return err
		}
		if name == "dn" {
			flush()
			cur = &Entry{DN: string(val), Attrs: map[string][][]byte{}}
			return nil
		}
		if cur == nil {
			return fmt.Errorf("%d행: dn 없이 속성이 왔다", lineNo)
		}
		cur.Attrs[name] = append(cur.Attrs[name], val)
		return nil
	}

	for sc.Scan() {
		lineNo++
		line := strings.TrimRight(sc.Text(), "\r")
		switch {
		case strings.HasPrefix(line, "#"):
			continue
		case line == "":
			if err := emit(); err != nil {
				return nil, err
			}
			flush()
		case strings.HasPrefix(line, " "):
			// LDIF 의 줄 잇기 — 빈칸으로 시작하면 앞줄의 계속이다.
			// 이걸 모르면 긴 DN 이 중간에서 잘린다.
			pending += line[1:]
		default:
			if err := emit(); err != nil {
				return nil, err
			}
			pending = line
		}
	}
	if err := sc.Err(); err != nil {
		return nil, err
	}
	if err := emit(); err != nil {
		return nil, err
	}
	flush()
	d.indexGroups()
	return d, nil
}

// parseLDIFLine 은 "이름: 값" 한 줄을 푼다.
// 콜론이 둘이면(::) 값이 base64 다 — objectGUID 처럼 글자가 아닌 값이나
// 앞이 빈칸으로 시작하는 값을 그렇게 싣는다 (RFC 2849).
func parseLDIFLine(line string) (name string, val []byte, err error) {
	i := strings.Index(line, ":")
	if i < 0 {
		return "", nil, fmt.Errorf("콜론이 없다: %q", line)
	}
	name = strings.ToLower(strings.TrimSpace(line[:i]))
	rest := line[i+1:]
	if strings.HasPrefix(rest, ":") {
		raw, e := base64.StdEncoding.DecodeString(
			strings.TrimSpace(rest[1:]))
		if e != nil {
			return "", nil, fmt.Errorf("%s: base64 가 아니다: %v",
				name, e)
		}
		return name, raw, nil
	}
	return name, []byte(strings.TrimSpace(rest)), nil
}

// ReloadFrom 은 파일을 다시 읽어 항목을 통째로 바꿔 끼운다.
//
// "AD 관리자가 계정을 지웠다" 를 흉내 내는 자리다. LDAP 의 delete 를
// 구현하지 않는 대신(이 서버는 읽기만 한다 — 3부 8장), 자료 파일을
// 고치고 SIGHUP 을 보내면 이 함수가 불린다. 잠금 기록은 그대로 둔다 —
// 계정을 지웠다고 남의 잠금이 풀리면 안 된다.
func (d *Dir) ReloadFrom(path string) error {
	fresh, err := LoadLDIFFile(path)
	if err != nil {
		return err
	}
	d.mu.Lock()
	defer d.mu.Unlock()
	d.entries, d.byDN, d.byUPN, d.groups =
		fresh.entries, fresh.byDN, fresh.byUPN, fresh.groups
	return nil
}

// DropEntryLDIF 는 LDIF 글에서 항목 하나를 지운 글을 돌려준다.
//
// 항목 블록(dn: 줄부터 다음 빈 줄까지)과, 그 DN 을 가리키는 그룹의
// member: 줄을 함께 뺀다. AD 도 사람을 지우면 그룹의 member 에서
// 같이 사라진다 — 그래야 memberOf 가 남지 않는다. O(줄 수).
func DropEntryLDIF(src, dn string) string {
	want := normDN(dn)
	var out []string
	skipping := false
	for _, line := range strings.Split(src, "\n") {
		switch {
		case skipping:
			if strings.TrimSpace(line) == "" {
				skipping = false
				out = append(out, line)
			}
			continue
		case strings.HasPrefix(line, "dn: ") &&
			normDN(strings.TrimPrefix(line, "dn: ")) == want:
			skipping = true
			continue
		case strings.HasPrefix(line, "member: ") &&
			normDN(strings.TrimPrefix(line, "member: ")) == want:
			continue
		}
		out = append(out, line)
	}
	return strings.Join(out, "\n")
}

func (d *Dir) add(e *Entry) {
	// distinguishedName 은 AD 가 늘 함께 주는 값이라 없으면 채워 둔다.
	if _, ok := e.Attrs["distinguishedname"]; !ok {
		e.Attrs["distinguishedname"] = [][]byte{[]byte(e.DN)}
	}
	d.entries = append(d.entries, e)
	d.byDN[normDN(e.DN)] = e
	if upn := e.First("userPrincipalName"); upn != "" {
		d.byUPN[strings.ToLower(upn)] = e
	}
}

// indexGroups 는 group 항목의 member 를 뒤집어 "사람 → 그룹" 표를
// 만든다.
//
// AD 도 이렇게 한다. 저장된 것은 그룹 쪽의 member 하나뿐이고,
// memberOf 는 물어볼 때마다 계산해서 보여 주는 값이다.
// 그 비대칭 때문에 7부의 group-ldap-mapper 에 "어느 쪽을 읽을 것인가"
// 라는 설정 칸이 따로 있다.
func (d *Dir) indexGroups() {
	for _, e := range d.entries {
		if !e.hasObjectClass("group") {
			continue
		}
		for _, m := range e.Attrs["member"] {
			key := normDN(string(m))
			d.groups[key] = append(d.groups[key], e.DN)
		}
	}
}

func (e *Entry) hasObjectClass(want string) bool {
	for _, v := range e.Attrs["objectclass"] {
		if strings.EqualFold(string(v), want) {
			return true
		}
	}
	return false
}

// ── 찾기 ─────────────────────────────────────────────────────────────

// Count 는 읽어 들인 항목 수다. 띄울 때 한 줄 찍는 용도.
func (d *Dir) Count() int { return len(d.entries) }

func (d *Dir) Get(dn string) *Entry { return d.byDN[normDN(dn)] }

// MemberOf 는 그 사람이 속한 그룹의 DN 목록이다.
func (d *Dir) MemberOf(dn string) []string {
	return d.groups[normDN(dn)]
}

// ── 바인드 ───────────────────────────────────────────────────────────

// Bind 는 "이 사람이 맞는가" 에 답한다.
//
// 실패하면 언제나 invalidCredentials(49)를 돌려준다. 이유는 진단 문구의
// "data XXX" 로만 알린다 — AD 가 그렇게 한다. 결과 코드를 이유마다
// 다르게 주면 남이 계정 목록을 만들 수 있기 때문이다(1부 5장의 그
// 원칙이다).
func (d *Dir) Bind(dn, password string) (int, string) {
	d.mu.Lock()
	defer d.mu.Unlock()

	// 익명 바인드와 빈 비밀번호는 받지 않는다.
	// 옛 서버 중에는 빈 비밀번호를 성공으로 처리해, 인증을 통째로
	// 건너뛰게 만든 것이 있었다. AD 도 요즘은 막아 둔다.
	if dn == "" || password == "" {
		return proto.ResultInvalidCredentials,
			adDiag("익명·빈 비밀번호는 안 받는다", adNoSuchUser)
	}

	e := d.byDN[normDN(dn)]
	if e == nil {
		e = d.byUPN[strings.ToLower(dn)] // AD 는 UPN 으로도 받아 준다
	}
	if e == nil {
		return proto.ResultInvalidCredentials,
			adDiag("그런 계정이 없다", adNoSuchUser)
	}

	key := normDN(e.DN)
	now := d.now()
	if st := d.fails[key]; st != nil && now.Before(st.until) {
		return proto.ResultInvalidCredentials,
			adDiag("계정이 잠겼다", adLocked)
	}

	if e.First("demoPassword") != password {
		d.noteFailure(key, now)
		return proto.ResultInvalidCredentials,
			adDiag("비밀번호가 틀렸다", adBadPassword)
	}

	// 꺼짐은 비밀번호가 맞은 뒤에야 알려 준다. AD 가 그렇다 — 안 그러면
	// 비밀번호 없이도 "이 계정이 살아 있나" 를 알아낼 수 있다.
	// 그래서 533 은 "비밀번호는 맞았다" 는 뜻이기도 하다(3부 5장).
	if e.disabled() {
		return proto.ResultInvalidCredentials,
			adDiag("계정이 꺼져 있다", adDisabled)
	}

	delete(d.fails, key) // 성공하면 세어 둔 실패를 지운다
	return proto.ResultSuccess, ""
}

// noteFailure 는 실패를 세고, 창 안에서 기준을 넘으면 잠근다.
func (d *Dir) noteFailure(key string, now time.Time) {
	st := d.fails[key]
	if st == nil || now.Sub(st.first) > lockWindow {
		st = &failState{first: now}
		d.fails[key] = st
	}
	st.count++
	if st.count >= lockThreshold {
		st.until = now.Add(lockDuration)
	}
}

func (e *Entry) disabled() bool {
	return e.uac()&uacAccountDisable != 0
}

func (e *Entry) uac() int {
	var n int
	_, err := fmt.Sscanf(e.First("userAccountControl"), "%d", &n)
	if err != nil {
		return uacNormalAccount
	}
	return n
}

// adDiag 는 AD 가 내는 진단 문구의 모양을 흉내 낸다.
// 진짜 AD 는 이렇게 생겼다:
//
//	80090308: LdapErr: DSID-0C09042F, comment:
//	AcceptSecurityContext error, data 52e, v4563
func adDiag(why, code string) string {
	return fmt.Sprintf(
		"80090308: LdapErr: DSID-0C09042F, comment: "+
			"AcceptSecurityContext error, data %s, v4563 (%s)",
		code, why)
}

// ── 검색 ─────────────────────────────────────────────────────────────

// Search 는 base 아래에서 scope 만큼 훑으며 필터에 맞는 항목을 모은다.
// 시간 O(항목 수 × 필터 크기). 우리 자료는 15건이라 이 정도면 충분하다.
func (d *Dir) Search(base string, scope int, f proto.Filter) []*Entry {
	nb := normDN(base)
	if _, ok := d.byDN[nb]; !ok {
		return nil // 없는 base — 진짜 AD 는 noSuchObject 를 낸다
	}
	var out []*Entry
	for _, e := range d.entries {
		if !inScope(normDN(e.DN), nb, scope) {
			continue
		}
		if d.match(e, f) {
			out = append(out, e)
		}
	}
	return out
}

// inScope 는 "이 항목이 그 범위 안인가" 를 DN 의 생김새만으로 판단한다.
// DN 은 아래에서 위로 적히므로, 아래에 있는 항목일수록 base 를 꼬리로
// 갖는다.
func inScope(dn, base string, scope int) bool {
	switch scope {
	case proto.ScopeBaseObject:
		return dn == base
	case proto.ScopeSingleLevel:
		if dn == base || !strings.HasSuffix(dn, ","+base) {
			return false
		}
		// 바로 아래 한 층만 — 앞쪽에 쉼표가 더 있으면 더 깊다.
		head := strings.TrimSuffix(dn, ","+base)
		return !strings.Contains(head, ",")
	case proto.ScopeWholeSubtree:
		return dn == base || strings.HasSuffix(dn, ","+base)
	}
	return false
}

// values 는 필터가 볼 값들을 준다. memberOf 는 여기서 계산해 끼워
// 넣는다 — 저장된 값이 아니지만 검색에서는 진짜 속성처럼 보여야 한다.
func (d *Dir) values(e *Entry, attr string) [][]byte {
	name := strings.ToLower(attr)
	if name == "memberof" {
		var out [][]byte
		for _, g := range d.MemberOf(e.DN) {
			out = append(out, []byte(g))
		}
		return out
	}
	if neverReturn[name] {
		return nil
	}
	return e.Attrs[name]
}

// match 는 필터 나무를 훑으며 이 항목이 조건에 맞는지 본다.
// 값 비교는 대소문자를 가리지 않는다 — AD 의 기본 동작이다.
func (d *Dir) match(e *Entry, f proto.Filter) bool {
	switch v := f.(type) {
	case *proto.And:
		for _, s := range v.Subs {
			if !d.match(e, s) {
				return false
			}
		}
		return true
	case *proto.Or:
		for _, s := range v.Subs {
			if d.match(e, s) {
				return true
			}
		}
		return false
	case *proto.Not:
		return !d.match(e, v.Sub)
	case *proto.Present:
		return len(d.values(e, v.Attr)) > 0
	case *proto.Equal:
		for _, got := range d.values(e, v.Attr) {
			if strings.EqualFold(string(got), v.Value) {
				return true
			}
		}
		return false
	case *proto.Approx:
		// 진짜 AD 는 발음이 비슷한 것까지 찾는다. 우리는 = 과 같게
		// 둔다.
		return d.match(e, &proto.Equal{Attr: v.Attr, Value: v.Value})
	case *proto.GreaterOrEqual:
		return d.compare(e, v.Attr, v.Value, true)
	case *proto.LessOrEqual:
		return d.compare(e, v.Attr, v.Value, false)
	case *proto.Substrings:
		return d.matchSubstrings(e, v)
	}
	return false
}

func (d *Dir) compare(e *Entry, attr, want string, ge bool) bool {
	for _, got := range d.values(e, attr) {
		s := strings.ToLower(string(got))
		w := strings.ToLower(want)
		if (ge && s >= w) || (!ge && s <= w) {
			return true
		}
	}
	return false
}

func (d *Dir) matchSubstrings(e *Entry, v *proto.Substrings) bool {
	for _, raw := range d.values(e, v.Attr) {
		s := strings.ToLower(string(raw))
		rest := s
		if v.Initial != "" {
			if !strings.HasPrefix(rest, strings.ToLower(v.Initial)) {
				continue
			}
			rest = rest[len(v.Initial):]
		}
		ok := true
		for _, a := range v.Any {
			i := strings.Index(rest, strings.ToLower(a))
			if i < 0 {
				ok = false
				break
			}
			rest = rest[i+len(a):]
		}
		if !ok {
			continue
		}
		if v.Final != "" && !strings.HasSuffix(rest,
			strings.ToLower(v.Final)) {
			continue
		}
		return true
	}
	return false
}

// ── 결과에 실을 속성 고르기 ──────────────────────────────────────────

// Attributes 는 검색 결과에 실을 속성을 고른다.
//
// want 가 비었거나 "*" 이면 전부, 아니면 물어본 것만. 물어본 이름을
// 그대로 돌려주는 것이 중요하다 — 소문자로 바꿔 보내면 Keycloak 의
// 매퍼가 자기가 물은 이름과 다르다고 못 알아보는 일이 생긴다.
func (d *Dir) Attributes(e *Entry, want []string) []proto.Attribute {
	all := len(want) == 0
	for _, w := range want {
		if w == "*" {
			all = true
		}
	}
	if all {
		return d.allAttributes(e)
	}
	var out []proto.Attribute
	for _, w := range want {
		if neverReturn[strings.ToLower(w)] {
			continue
		}
		vals := d.values(e, w)
		if len(vals) == 0 {
			// 없는 칸은 아예 빼고 보낸다. 빈 값으로 채우지 않는다.
			continue
		}
		out = append(out, proto.Attribute{Name: w, Values: vals})
	}
	return out
}

// allAttributes 는 저장된 속성 전부에 계산 속성 memberOf 를 더해 준다.
// 순서를 고정하려고 항목이 읽힌 차례를 따르지 않고 이름순으로 낸다 —
// 지도(map)를 그냥 훑으면 캡처가 돌릴 때마다 달라진다.
func (d *Dir) allAttributes(e *Entry) []proto.Attribute {
	names := make([]string, 0, len(e.Attrs)+1)
	for n := range e.Attrs {
		if !neverReturn[n] {
			names = append(names, n)
		}
	}
	if len(d.MemberOf(e.DN)) > 0 {
		names = append(names, "memberof")
	}
	sortStrings(names)
	out := make([]proto.Attribute, 0, len(names))
	for _, n := range names {
		out = append(out,
			proto.Attribute{Name: n, Values: d.values(e, n)})
	}
	return out
}

// 표준 라이브러리의 sort 를 쓰지 않고 여기 적어 둔 이유는 없다 — 이름이
// 열 몇 개뿐이라 삽입 정렬이 더 짧고 읽기 쉽다. O(n²) 이지만 n<20.
func sortStrings(s []string) {
	for i := 1; i < len(s); i++ {
		for j := i; j > 0 && s[j] < s[j-1]; j-- {
			s[j], s[j-1] = s[j-1], s[j]
		}
	}
}
