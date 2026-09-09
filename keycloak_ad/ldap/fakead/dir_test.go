package fakead

import (
	"bytes"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"treasure/keycloak_ad/ldap/proto"
)

const base = "DC=ad,DC=campus,DC=example"

func load(t *testing.T) *Dir {
	t.Helper()
	d, err := LoadLDIFFile("../../data/campus.ldif")
	if err != nil {
		t.Fatalf("LDIF 를 못 읽는다: %v", err)
	}
	now := time.Date(2026, 9, 8, 9, 0, 0, 0, time.UTC)
	d.now = func() time.Time { return now }
	return d
}

func TestLoadCounts(t *testing.T) {
	d := load(t)
	// 꼭대기 1 · OU 4 · 사람 6 · 서비스 계정 1 · 그룹 3 = 15
	if n := len(d.entries); n != 15 {
		t.Errorf("항목 %d개, 원하는 것 15", n)
	}
}

// DN 은 대소문자를 가리지 않는다. AD 도 그렇고, 그래서 Keycloak 이
// 저장해 둔 DN 과 사용자가 친 DN 의 대소문자가 달라도 같은 사람이어야
// 한다.
func TestDNIsCaseInsensitive(t *testing.T) {
	d := load(t)
	want := "CN=Kim Minji,OU=Students," + base
	for _, dn := range []string{
		want,
		strings.ToLower(want),
		strings.ToUpper(want),
		"cn=Kim Minji, ou=Students, dc=ad, dc=campus, dc=example",
	} {
		if e := d.Get(dn); e == nil {
			t.Errorf("%q 를 못 찾는다", dn)
		}
	}
	if d.Get("CN=없는사람,"+base) != nil {
		t.Error("없는 DN 이 찾아졌다")
	}
}

// objectGUID 는 16바이트 이진값이다. 글자로 다루면 0x00 에서 잘린다.
func TestObjectGUIDIsSixteenRawBytes(t *testing.T) {
	d := load(t)
	e := d.Get("CN=Kim Minji,OU=Students," + base)
	if e == nil {
		t.Fatal("민지를 못 찾는다")
	}
	g := e.Attrs["objectguid"]
	if len(g) != 1 || len(g[0]) != 16 {
		t.Fatalf("objectGUID 가 %d개 · 첫 값 %d바이트", len(g), len(g[0]))
	}
	// LDIF 의 base64 를 제대로 풀었는지 첫 바이트로 확인한다.
	if g[0][0] != 0x98 || g[0][1] != 0xD3 {
		t.Errorf("objectGUID 앞머리 = % X", g[0][:4])
	}
}

// memberOf 는 저장된 값이 아니라 계산해서 보여 주는 값이다.
// AD 가 그렇게 하고, 그 비대칭이 7부 매퍼 설정의 핵심이다.
func TestMemberOfIsComputed(t *testing.T) {
	d := load(t)
	minji := "CN=Kim Minji,OU=Students," + base
	e := d.Get(minji)
	if _, stored := e.Attrs["memberof"]; stored {
		t.Error("memberOf 가 저장돼 있다 — 계산해야 한다")
	}
	got := d.MemberOf(minji)
	if len(got) != 2 {
		t.Fatalf("민지의 그룹 %d개: %v", len(got), got)
	}
	joined := strings.Join(got, " ")
	for _, want := range []string{"lunch-users", "campus-all"} {
		if !strings.Contains(joined, want) {
			t.Errorf("%s 가 없다: %v", want, got)
		}
	}
	if strings.Contains(joined, "lunch-admins") {
		t.Error("민지는 lunch-admins 가 아니다")
	}
}

func TestMemberOfForAdmin(t *testing.T) {
	d := load(t)
	got := d.MemberOf("CN=Lee Sohee,OU=Staff," + base)
	if len(got) != 3 {
		t.Errorf("소희의 그룹 %d개: %v", len(got), got)
	}
}

// 졸업생은 campus-all 에만 있다 — 로그인은 되는데 학식은 못 쓰는 상태.
func TestGraduateHasNoLunchGroup(t *testing.T) {
	d := load(t)
	got := d.MemberOf("CN=Choi Yuna,OU=Students," + base)
	if len(got) != 1 || !strings.Contains(got[0], "campus-all") {
		t.Errorf("유나의 그룹 = %v", got)
	}
}

// ── 바인드 ───────────────────────────────────────────────────────────

func TestBindSuccess(t *testing.T) {
	d := load(t)
	dn := "CN=Kim Minji,OU=Students," + base
	code, diag := d.Bind(dn, "Passw0rd!-demo")
	if code != proto.ResultSuccess {
		t.Errorf("코드 %d · %s", code, diag)
	}
}

// AD 는 실패 이유를 diagnosticMessage 의 "data XXX" 로 알려 준다.
// 그 숫자를 읽을 줄 아는 것이 7부 진단의 절반이다.
func TestBindFailuresCarryADCodes(t *testing.T) {
	d := load(t)
	cases := []struct {
		name, dn, pass, want string
	}{
		{"비밀번호 틀림", "CN=Kim Minji,OU=Students," + base,
			"틀린것", "data 52e"},
		{"없는 계정", "CN=없는사람,OU=Students," + base,
			"Passw0rd!-demo", "data 525"},
		{"비활성 계정", "CN=Oh Jisoo,OU=Staff," + base,
			"Passw0rd!-demo", "data 533"},
	}
	for _, c := range cases {
		code, diag := d.Bind(c.dn, c.pass)
		if code != proto.ResultInvalidCredentials {
			t.Errorf("%s: 코드 %d, 원하는 것 49", c.name, code)
		}
		if !strings.Contains(diag, c.want) {
			t.Errorf("%s: 진단 %q 에 %q 가 없다", c.name, diag, c.want)
		}
	}
}

// 비활성 계정은 **비밀번호가 맞아도** 못 들어온다.
func TestDisabledAccountRejectedWithRightPassword(t *testing.T) {
	d := load(t)
	code, diag := d.Bind("CN=Oh Jisoo,OU=Staff,"+base, "Passw0rd!-demo")
	if code == proto.ResultSuccess {
		t.Fatal("비활성 계정이 통과했다")
	}
	if !strings.Contains(diag, "533") {
		t.Errorf("진단 = %q", diag)
	}
}

// UPN 으로도 바인드할 수 있어야 한다. AD 가 그렇고,
// 7부의 "로그인 아이디를 무엇으로 할 것인가" 가 여기서 갈린다.
func TestBindByUPN(t *testing.T) {
	d := load(t)
	code, _ := d.Bind("minji@ad.campus.example", "Passw0rd!-demo")
	if code != proto.ResultSuccess {
		t.Errorf("UPN 바인드 실패: %d", code)
	}
}

// 익명 바인드(이름·비밀번호 둘 다 빈 것)는 거절한다. AD 의 기본과 같다.
func TestAnonymousBindRejected(t *testing.T) {
	d := load(t)
	if code, _ := d.Bind("", ""); code == proto.ResultSuccess {
		t.Error("익명 바인드가 통과했다")
	}
}

// 비밀번호가 빈 채로 오는 것도 거절한다 — "unauthenticated bind" 라고
// 하며, 옛 서버 중에는 이걸 성공으로 처리해 인증을 통째로 건너뛰게 한
// 것이 있었다.
func TestEmptyPasswordRejected(t *testing.T) {
	d := load(t)
	code, _ := d.Bind("CN=Kim Minji,OU=Students,"+base, "")
	if code == proto.ResultSuccess {
		t.Error("빈 비밀번호가 통과했다")
	}
}

// 다섯 번 틀리면 잠긴다. 그다음부터는 **맞는 비밀번호도** 안 통한다.
func TestLockoutAfterFiveFailures(t *testing.T) {
	d := load(t)
	dn := "CN=Park Hana,OU=Students," + base
	for i := 0; i < 5; i++ {
		if _, diag := d.Bind(dn, "틀린것"); !strings.Contains(diag, "52e") {
			t.Fatalf("%d번째 실패의 진단이 이상하다: %s", i+1, diag)
		}
	}
	code, diag := d.Bind(dn, "Passw0rd!-demo")
	if code == proto.ResultSuccess {
		t.Fatal("잠겼는데 통과했다")
	}
	if !strings.Contains(diag, "data 775") {
		t.Errorf("잠김 진단 = %q", diag)
	}
}

// 창(10분)이 지나면 실패 횟수는 잊힌다.
func TestFailureWindowExpires(t *testing.T) {
	now := time.Date(2026, 9, 8, 9, 0, 0, 0, time.UTC)
	d := load(t)
	d.now = func() time.Time { return now }
	dn := "CN=Park Hana,OU=Students," + base
	for i := 0; i < 4; i++ {
		d.Bind(dn, "틀린것")
	}
	now = now.Add(11 * time.Minute)
	d.Bind(dn, "틀린것") // 창이 지나 1번째로 다시 센다
	if code, diag := d.Bind(dn, "Passw0rd!-demo"); code != proto.ResultSuccess {
		t.Errorf("창이 지났는데 막혔다: %d %s", code, diag)
	}
}

// 성공하면 세어 둔 실패가 지워진다.
func TestSuccessResetsFailures(t *testing.T) {
	d := load(t)
	dn := "CN=Park Hana,OU=Students," + base
	for i := 0; i < 4; i++ {
		d.Bind(dn, "틀린것")
	}
	if code, _ := d.Bind(dn, "Passw0rd!-demo"); code != proto.ResultSuccess {
		t.Fatal("네 번 틀린 뒤 맞는 비밀번호가 막혔다")
	}
	for i := 0; i < 4; i++ {
		d.Bind(dn, "틀린것")
	}
	if code, _ := d.Bind(dn, "Passw0rd!-demo"); code != proto.ResultSuccess {
		t.Error("성공이 실패 횟수를 지우지 않았다")
	}
}

// ── 검색 ─────────────────────────────────────────────────────────────

func mustFilter(t *testing.T, s string) proto.Filter {
	t.Helper()
	f, err := proto.ParseFilterString(s)
	if err != nil {
		t.Fatalf("%s: %v", s, err)
	}
	return f
}

func TestSearchScopes(t *testing.T) {
	d := load(t)
	all := mustFilter(t, "(objectClass=*)")
	cases := []struct {
		name  string
		base  string
		scope int
		want  int
	}{
		{"base 는 그 하나만", base, proto.ScopeBaseObject, 1},
		{"one 은 바로 아래만", base, proto.ScopeSingleLevel, 4},
		{"sub 는 전부", base, proto.ScopeWholeSubtree, 15},
		{"Students 아래", "OU=Students," + base,
			proto.ScopeWholeSubtree, 4},
		{"Groups 아래 한 층", "OU=Groups," + base,
			proto.ScopeSingleLevel, 3},
	}
	for _, c := range cases {
		got := d.Search(c.base, c.scope, all)
		if len(got) != c.want {
			t.Errorf("%s: %d건, 원하는 것 %d", c.name, len(got), c.want)
		}
	}
}

func TestSearchMissingBaseIsEmpty(t *testing.T) {
	d := load(t)
	got := d.Search("OU=없는곳,"+base, proto.ScopeWholeSubtree,
		mustFilter(t, "(objectClass=*)"))
	if len(got) != 0 {
		t.Errorf("없는 base 인데 %d건", len(got))
	}
}

// Keycloak 이 AD 사용자를 찾을 때 실제로 보내는 필터.
func TestSearchKeycloakUserFilter(t *testing.T) {
	d := load(t)
	f := mustFilter(t, "(&(objectClass=person)"+
		"(objectClass=organizationalPerson)(objectClass=user)"+
		"(sAMAccountName=minji))")
	got := d.Search(base, proto.ScopeWholeSubtree, f)
	if len(got) != 1 {
		t.Fatalf("%d건 — 민지 하나여야 한다", len(got))
	}
	if !strings.Contains(got[0].DN, "Kim Minji") {
		t.Errorf("찾은 것 = %s", got[0].DN)
	}
}

// 값 비교는 대소문자를 가리지 않는다 — AD 의 기본 동작이다.
func TestSearchValueIsCaseInsensitive(t *testing.T) {
	d := load(t)
	for _, s := range []string{"(sAMAccountName=minji)",
		"(sAMAccountName=MINJI)", "(samaccountname=MinJi)"} {
		if n := len(d.Search(base, proto.ScopeWholeSubtree,
			mustFilter(t, s))); n != 1 {
			t.Errorf("%s → %d건", s, n)
		}
	}
}

func TestSearchFilterVariants(t *testing.T) {
	d := load(t)
	cases := []struct {
		filter string
		want   int
	}{
		{"(objectClass=user)", 7},
		{"(objectClass=group)", 3},
		{"(mail=*)", 6},
		{"(!(mail=*))", 9},
		{"(sAMAccountName=minji)", 1},
		{"(sn=Kim)", 2},
		{"(cn=Kim*)", 2},
		{"(cn=*Minji)", 1},
		{"(|(sAMAccountName=minji)(sAMAccountName=prof.kim))", 2},
		{"(&(objectClass=user)(userAccountControl=514))", 1},
		{"(title=학부 인턴)", 1},
		{"(cn=없는이름)", 0},
	}
	for _, c := range cases {
		got := d.Search(base, proto.ScopeWholeSubtree,
			mustFilter(t, c.filter))
		if len(got) != c.want {
			t.Errorf("%s → %d건, 원하는 것 %d", c.filter, len(got), c.want)
		}
	}
}

// memberOf 로도 찾을 수 있어야 한다. 계산해서 만든 값이지만
// 검색에서는 진짜 속성처럼 보여야 한다 — AD 가 그렇다.
func TestSearchByMemberOf(t *testing.T) {
	d := load(t)
	f := mustFilter(t,
		"(memberOf=CN=lunch-admins,OU=Groups,DC=ad,DC=campus,DC=example)")
	got := d.Search(base, proto.ScopeWholeSubtree, f)
	if len(got) != 1 || !strings.Contains(got[0].DN, "Lee Sohee") {
		t.Errorf("lunch-admins 검색 = %v", dns(got))
	}
}

// ── 속성 고르기 ──────────────────────────────────────────────────────

// 비밀번호 칸은 **어떤 검색으로도** 나가면 안 된다.
func TestPasswordNeverReturned(t *testing.T) {
	d := load(t)
	e := d.Get("CN=Kim Minji,OU=Students," + base)
	for _, want := range [][]string{nil, {"*"}, {"demoPassword"},
		{"DEMOPASSWORD"}, {"cn", "demopassword"}} {
		for _, a := range d.Attributes(e, want) {
			if strings.EqualFold(a.Name, "demoPassword") {
				t.Errorf("%v 로 물으니 비밀번호가 나왔다", want)
			}
		}
	}
}

func TestAttributesSelectsRequested(t *testing.T) {
	d := load(t)
	e := d.Get("CN=Kim Minji,OU=Students," + base)
	got := d.Attributes(e, []string{"cn", "mail"})
	if len(got) != 2 {
		t.Fatalf("속성 %d개: %v", len(got), got)
	}
	// 이름은 요청한 대로 돌려준다 — 소문자로 바꿔 보내면
	// Keycloak 쪽 매퍼가 못 알아보는 일이 생긴다.
	if got[0].Name != "cn" || got[1].Name != "mail" {
		t.Errorf("이름 = %s, %s", got[0].Name, got[1].Name)
	}
}

func TestAttributesEmptyMeansAll(t *testing.T) {
	d := load(t)
	e := d.Get("CN=Kim Minji,OU=Students," + base)
	got := d.Attributes(e, nil)
	if len(got) < 10 {
		t.Errorf("전부 달라고 했는데 %d개뿐이다", len(got))
	}
	var names []string
	for _, a := range got {
		names = append(names, strings.ToLower(a.Name))
	}
	joined := strings.Join(names, " ")
	for _, want := range []string{"objectguid", "samaccountname",
		"memberof", "useraccountcontrol"} {
		if !strings.Contains(joined, want) {
			t.Errorf("%s 가 빠졌다: %v", want, names)
		}
	}
}

// memberOf 는 물었을 때만 계산하지만, 물으면 반드시 나와야 한다.
func TestAttributesIncludesComputedMemberOf(t *testing.T) {
	d := load(t)
	e := d.Get("CN=Kim Minji,OU=Students," + base)
	got := d.Attributes(e, []string{"memberOf"})
	if len(got) != 1 || len(got[0].Values) != 2 {
		t.Fatalf("memberOf = %v", got)
	}
}

// 없는 속성을 물으면 그 칸은 아예 빠진다. 빈 값으로 채우지 않는다.
func TestAttributesSkipsMissing(t *testing.T) {
	d := load(t)
	e := d.Get("CN=lunch-users,OU=Groups," + base)
	got := d.Attributes(e, []string{"cn", "mail"})
	if len(got) != 1 || got[0].Name != "cn" {
		t.Errorf("그룹에 mail 이 없는데 = %v", got)
	}
}

func TestUserAccountControlValues(t *testing.T) {
	d := load(t)
	cases := map[string]string{
		"CN=Kim Minji,OU=Students," + base: "512",
		"CN=Kim Junho,OU=Staff," + base:    "66048",
		"CN=Oh Jisoo,OU=Staff," + base:     "514",
	}
	for dn, want := range cases {
		e := d.Get(dn)
		if e == nil {
			t.Fatalf("%s 를 못 찾는다", dn)
		}
		got := e.Attrs["useraccountcontrol"]
		if len(got) != 1 || !bytes.Equal(got[0], []byte(want)) {
			t.Errorf("%s 의 uAC = %s, 원하는 것 %s", dn, got, want)
		}
	}
}

func dns(es []*Entry) []string {
	var out []string
	for _, e := range es {
		out = append(out, e.DN)
	}
	return out
}

// 진짜 AD 는 비밀번호를 먼저 맞혀 보고, 맞았을 때만 "꺼져 있다(533)" 를
// 알려 준다. 틀리면 꺼진 계정이라도 52e 다 — 계정 상태를 비밀번호 없이
// 알아낼 수 없게 하려는 것이다. 3부 5장이 그렇게 가르치므로 흉내도
// 같아야 한다.
func TestDisabledAccountWithWrongPasswordIs52e(t *testing.T) {
	d := load(t)
	_, diag := d.Bind("CN=Oh Jisoo,OU=Staff,"+base, "틀린것")
	if !strings.Contains(diag, "data 52e") {
		t.Errorf("꺼진 계정 + 틀린 비밀번호 = %q, 원하는 것 52e", diag)
	}
}

// ReloadFrom 은 "AD 관리자가 계정을 지웠다" 를 흉내 내는 데 쓴다 —
// 7부에서 Keycloak 이 사라진 사람을 어떻게 알아채는지 보는 실험이다.
// 그룹의 member 에서도 빠져야 memberOf 가 같이 사라진다.
func TestReloadDropsDeletedEntry(t *testing.T) {
	d := load(t)
	yuna := "CN=Choi Yuna,OU=Students," + base
	if d.Get(yuna) == nil || len(d.MemberOf(yuna)) == 0 {
		t.Fatal("시작 자료에 유나가 없다")
	}
	src, err := os.ReadFile("../../data/campus.ldif")
	if err != nil {
		t.Fatal(err)
	}
	trimmed := DropEntryLDIF(string(src), yuna)
	p := filepath.Join(t.TempDir(), "campus.ldif")
	if err := os.WriteFile(p, []byte(trimmed), 0o600); err != nil {
		t.Fatal(err)
	}
	if err := d.ReloadFrom(p); err != nil {
		t.Fatalf("다시 읽기: %v", err)
	}
	if d.Count() != 14 {
		t.Errorf("항목 %d개, 원하는 것 14", d.Count())
	}
	if d.Get(yuna) != nil {
		t.Error("지운 항목이 아직 있다")
	}
	if len(d.MemberOf(yuna)) != 0 {
		t.Errorf("지운 사람의 memberOf 가 남았다: %v", d.MemberOf(yuna))
	}
	minji := "CN=Kim Minji,OU=Students," + base
	code, _ := d.Bind(minji, "Passw0rd!-demo")
	if code != proto.ResultSuccess {
		t.Error("다시 읽은 뒤 민지가 못 들어온다")
	}
}
