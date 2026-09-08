package miniidp

import (
	"io"
	"strings"
	"testing"

	"treasure/keycloak_ad/ldap/fakead"
)

// 진짜 가짜 AD 를 띄워 놓고 시험한다 — 3부에서 만든 그 서버다.
func startAD(t *testing.T) string {
	t.Helper()
	d, err := fakead.LoadLDIFFile("../../data/campus.ldif")
	if err != nil {
		t.Fatal(err)
	}
	srv := fakead.NewServer(d, io.Discard)
	if err := srv.ListenPlain("127.0.0.1:0"); err != nil {
		t.Fatal(err)
	}
	t.Cleanup(srv.Close)
	return srv.Addr()
}

func adDir(t *testing.T) Directory {
	t.Helper()
	return NewLDAPDirectory(LDAPConfig{
		Addr:   startAD(t),
		BaseDN: "DC=ad,DC=campus,DC=example",
		BindDN: "CN=svc-keycloak,OU=Service Accounts," +
			"DC=ad,DC=campus,DC=example",
		BindPassword: "Passw0rd!-demo",
	})
}

func TestLDAPAuthenticate(t *testing.T) {
	u, err := adDir(t).Authenticate("minji", "Passw0rd!-demo")
	if err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(u.DN, "Kim Minji") {
		t.Errorf("DN = %s", u.DN)
	}
	if u.Username != "minji" || u.Email != "minji@campus.example" {
		t.Errorf("사용자 = %+v", u)
	}
	if u.Name != "김민지" {
		t.Errorf("이름 = %q — displayName 을 골라야 한다", u.Name)
	}
	if len(u.Groups) != 2 {
		t.Fatalf("그룹 = %v", u.Groups)
	}
	// 그룹은 DN 이 아니라 이름만 실려야 한다.
	for _, g := range u.Groups {
		if strings.Contains(g, "=") || strings.Contains(g, ",") {
			t.Errorf("그룹에 DN 이 그대로 있다: %q", g)
		}
	}
}

func TestLDAPWrongPassword(t *testing.T) {
	_, err := adDir(t).Authenticate("minji", "틀린것")
	if err == nil {
		t.Fatal("틀린 비밀번호가 통과했다")
	}
	// AD 의 진단이 그대로 올라와야 한다 — 7부 진단의 재료다.
	if !strings.Contains(err.Error(), "data 52e") {
		t.Errorf("진단이 없다: %v", err)
	}
}

// 꺼진 계정은 비밀번호가 맞아도 못 들어온다 (3부 2·5장).
func TestLDAPDisabledAccount(t *testing.T) {
	_, err := adDir(t).Authenticate("jisoo.oh", "Passw0rd!-demo")
	if err == nil {
		t.Fatal("꺼진 계정이 통과했다")
	}
	if !strings.Contains(err.Error(), "data 533") {
		t.Errorf("진단이 없다: %v", err)
	}
}

func TestLDAPUnknownUser(t *testing.T) {
	_, err := adDir(t).Authenticate("없는사람", "Passw0rd!-demo")
	if err == nil {
		t.Fatal("없는 사람이 통과했다")
	}
	// 어느 쪽이 틀렸는지 말하지 않는다.
	if strings.Contains(err.Error(), "없는") &&
		!strings.Contains(err.Error(), "맞지 않습니다") {
		t.Errorf("계정 유무가 새어 나간다: %v", err)
	}
}

func TestLDAPEmptyInput(t *testing.T) {
	d := adDir(t)
	for _, c := range [][2]string{{"", "x"}, {"minji", ""}, {"", ""}} {
		if _, err := d.Authenticate(c[0], c[1]); err == nil {
			t.Errorf("%v 가 통과했다", c)
		}
	}
}

// 사용자가 친 값이 필터에 그대로 들어가면 안 된다 (3부 6장 퀴즈).
func TestLDAPFilterInjection(t *testing.T) {
	_, err := adDir(t).Authenticate("*)(objectClass=*", "Passw0rd!-demo")
	if err == nil {
		t.Fatal("필터 주입이 통과했다")
	}
	// "여럿이 걸렸다" 가 아니라 "못 찾았다" 여야 한다 —
	// 값이 제대로 감싸졌다면 그런 아이디는 없기 때문이다.
	if strings.Contains(err.Error(), "명이 걸렸습니다") {
		t.Errorf("필터가 열렸다: %v", err)
	}
}

// UPN 으로 로그인하게 둘 수도 있다 (7부에서 고르는 그 설정).
func TestLDAPUsernameAttrIsConfigurable(t *testing.T) {
	d := NewLDAPDirectory(LDAPConfig{
		Addr:   startAD(t),
		BaseDN: "DC=ad,DC=campus,DC=example",
		BindDN: "CN=svc-keycloak,OU=Service Accounts," +
			"DC=ad,DC=campus,DC=example",
		BindPassword: "Passw0rd!-demo",
		UsernameAttr: "userPrincipalName",
	})
	u, err := d.Authenticate("minji@ad.campus.example", "Passw0rd!-demo")
	if err != nil {
		t.Fatal(err)
	}
	if u.Username != "minji@ad.campus.example" {
		t.Errorf("사용자 = %q", u.Username)
	}
	// sAMAccountName 으로는 이제 못 들어온다 — 설정이 그렇게 바뀐 것이다.
	if _, err := d.Authenticate("minji", "Passw0rd!-demo"); err == nil {
		t.Error("설정과 다른 아이디로 통과했다")
	}
}

// 서비스 계정의 비밀번호가 틀리면 **모든 사람**이 못 들어온다.
func TestLDAPBadServiceAccount(t *testing.T) {
	d := NewLDAPDirectory(LDAPConfig{
		Addr:   startAD(t),
		BaseDN: "DC=ad,DC=campus,DC=example",
		BindDN: "CN=svc-keycloak,OU=Service Accounts," +
			"DC=ad,DC=campus,DC=example",
		BindPassword: "틀린것",
	})
	_, err := d.Authenticate("minji", "Passw0rd!-demo")
	if err == nil {
		t.Fatal("서비스 계정이 틀렸는데 통과했다")
	}
	if !strings.Contains(err.Error(), "서비스 계정") {
		t.Errorf("어디가 문제인지 안 알려 준다: %v", err)
	}
}
