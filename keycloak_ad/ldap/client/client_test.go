package client

import (
	"strings"
	"testing"
	"time"

	"treasure/keycloak_ad/ldap/proto"
)

// 시험은 가짜 AD 를 진짜로 띄워 놓고 한다. 흉내 낸 서버에 대고 하는
// 시험은 "우리 생각대로 도는가" 만 보여 주지, 진짜로 통하는지는 못
// 본다.
const (
	base = "DC=ad,DC=campus,DC=example"
	svc  = "CN=svc-keycloak,OU=Service Accounts," + base
	pw   = "Passw0rd!-demo"
)

// startFakeAD 는 out/ 에 로그를 남기지 않는 가짜 AD 를 하나 띄운다.
// 주소를 돌려주고, 시험이 끝나면 알아서 꺼진다.
func startFakeAD(t *testing.T) string {
	t.Helper()
	addr, stop := spawnFakeAD(t)
	t.Cleanup(stop)
	return addr
}

func TestBindAndSearch(t *testing.T) {
	addr := startFakeAD(t)
	c, err := Dial(addr, Options{Timeout: 5 * time.Second})
	if err != nil {
		t.Fatal(err)
	}
	defer c.Close()

	if err := c.Bind(svc, pw); err != nil {
		t.Fatalf("서비스 계정 바인드 실패: %v", err)
	}
	got, err := c.Search(base, proto.ScopeWholeSubtree,
		"(sAMAccountName=minji)", []string{"cn", "mail", "memberOf"})
	if err != nil {
		t.Fatal(err)
	}
	if len(got) != 1 {
		t.Fatalf("%d건 — 하나여야 한다", len(got))
	}
	e := got[0]
	if !strings.Contains(e.DN, "Kim Minji") {
		t.Errorf("DN = %s", e.DN)
	}
	if e.First("cn") != "Kim Minji" {
		t.Errorf("cn = %q", e.First("cn"))
	}
	if len(e.Attrs["memberof"]) != 2 {
		t.Errorf("memberOf = %v", e.Values("memberOf"))
	}
}

func TestBindWrongPasswordCarriesDiagnostic(t *testing.T) {
	addr := startFakeAD(t)
	c, _ := Dial(addr, Options{Timeout: 5 * time.Second})
	defer c.Close()
	err := c.Bind("CN=Kim Minji,OU=Students,"+base, "틀린것")
	if err == nil {
		t.Fatal("틀린 비밀번호가 통과했다")
	}
	// AD 의 진단 문구를 그대로 들고 와야 한다 — 7부 진단의 재료다.
	if !strings.Contains(err.Error(), "data 52e") {
		t.Errorf("오류에 진단이 없다: %v", err)
	}
	var be *BindError
	if !asBindError(err, &be) {
		t.Fatalf("BindError 가 아니다: %T", err)
	}
	if be.Code != proto.ResultInvalidCredentials {
		t.Errorf("코드 = %d", be.Code)
	}
	if be.ADCode() != "52e" {
		t.Errorf("AD 코드 = %q", be.ADCode())
	}
}

func TestSearchBeforeBindFails(t *testing.T) {
	addr := startFakeAD(t)
	c, _ := Dial(addr, Options{Timeout: 5 * time.Second})
	defer c.Close()
	if _, err := c.Search(base, proto.ScopeWholeSubtree,
		"(objectClass=*)", nil); err == nil {
		t.Error("바인드 전 검색이 통과했다")
	}
}

func TestSearchBadFilter(t *testing.T) {
	addr := startFakeAD(t)
	c, _ := Dial(addr, Options{Timeout: 5 * time.Second})
	defer c.Close()
	c.Bind(svc, pw)
	if _, err := c.Search(base, proto.ScopeWholeSubtree, "(cn=", nil); err == nil {
		t.Error("망가진 필터가 통과했다")
	}
}

// Trace 를 걸면 오간 바이트를 그대로 넘겨받는다.
// ldapcli 가 바이트를 풀어 보여 줄 수 있는 것이 이 갈고리 덕분이다.
func TestTraceSeesBothDirections(t *testing.T) {
	addr := startFakeAD(t)
	c, _ := Dial(addr, Options{Timeout: 5 * time.Second})
	defer c.Close()
	var sent, recv int
	c.Trace = func(dir string, raw []byte) {
		if len(raw) == 0 {
			t.Error("빈 바이트가 넘어왔다")
		}
		switch dir {
		case "→":
			sent++
		case "←":
			recv++
		default:
			t.Errorf("모르는 방향 %q", dir)
		}
	}
	c.Bind(svc, pw)
	if sent != 1 || recv != 1 {
		t.Errorf("보냄 %d · 받음 %d — 바인드는 한 번씩이다", sent, recv)
	}
}

// 여러 번 검색해도 messageID 가 겹치면 안 된다 — 답을 짝지을 수 없게
// 된다.
func TestMessageIDIncrements(t *testing.T) {
	addr := startFakeAD(t)
	c, _ := Dial(addr, Options{Timeout: 5 * time.Second})
	defer c.Close()
	var ids []int64
	c.Trace = func(dir string, raw []byte) {
		if dir != "→" {
			return
		}
		if m, err := proto.ParseMessage(raw); err == nil {
			ids = append(ids, m.ID)
		}
	}
	c.Bind(svc, pw)
	c.Search(base, proto.ScopeBaseObject, "(objectClass=*)", nil)
	c.Search(base, proto.ScopeBaseObject, "(objectClass=*)", nil)
	if len(ids) != 3 {
		t.Fatalf("보낸 통 %d개", len(ids))
	}
	for i := 1; i < len(ids); i++ {
		if ids[i] <= ids[i-1] {
			t.Errorf("messageID 가 안 늘어난다: %v", ids)
		}
	}
}

func TestDialUnreachable(t *testing.T) {
	// 127.0.0.1 의 1번 포트는 아무도 안 듣는다.
	if _, err := Dial("127.0.0.1:1",
		Options{Timeout: time.Second}); err == nil {
		t.Error("없는 서버에 붙었다")
	}
}
