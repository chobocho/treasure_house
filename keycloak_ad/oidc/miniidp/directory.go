// directory.go — AD 에 물어보는 쪽.
//
// Keycloak 의 **User Federation** 이 하는 일을 그대로 한다.
// 두 번 붙는다.
//
//  1. 서비스 계정으로 붙어  →  아이디로 그 사람의 DN 을 **찾는다**
//  2. 찾은 DN 으로 다시 붙어 →  비밀번호를 **확인한다**
//
// 왜 두 번인가: 사용자는 "minji" 라고 치지만 LDAP 의 바인드는 DN 을
// 요구한다. 그 DN 을 알아내려면 먼저 검색해야 하고, 검색부터 신분이
// 필요하다(3부 5·7장). 그래서 읽기 전용 서비스 계정이 하나 있어야 한다.
//
// 그리고 LDAP 은 **연결마다** 신분이 붙으므로(3부 5장), 사용자 확인은
// 반드시 다른 연결에서 해야 한다. 같은 연결에서 다시 바인드하면
// 서비스 계정 신분을 잃어 다음 사람을 못 찾는다.
package miniidp

import (
	"fmt"
	"strings"

	"treasure/keycloak_ad/ldap/client"
	"treasure/keycloak_ad/ldap/proto"
)

// LDAPConfig 는 7부에서 Keycloak 관리 화면에 채우게 될 칸들과 같다.
type LDAPConfig struct {
	Addr         string // ldap.ad.campus.example:636
	BaseDN       string // DC=ad,DC=campus,DC=example
	BindDN       string // CN=svc-keycloak,OU=Service Accounts,…
	BindPassword string
	UsernameAttr string // sAMAccountName 또는 userPrincipalName
	TLS          bool
	CAFile       string
	ServerName   string
}

type ldapDirectory struct{ cfg LDAPConfig }

func NewLDAPDirectory(cfg LDAPConfig) Directory {
	if cfg.UsernameAttr == "" {
		cfg.UsernameAttr = "sAMAccountName"
	}
	return &ldapDirectory{cfg: cfg}
}

func (d *ldapDirectory) dial() (*client.Conn, error) {
	return client.Dial(d.cfg.Addr, client.Options{
		TLS: d.cfg.TLS, CAFile: d.cfg.CAFile,
		ServerName: d.cfg.ServerName,
	})
}

// 가져올 속성. 필요한 것만 적는 이유는 3부 6장에 있다 —
// 전부 달라고 하면 사진 같은 큰 칸까지 딸려 온다.
var wantAttrs = []string{
	"distinguishedName", "sAMAccountName", "userPrincipalName",
	"cn", "displayName", "mail", "memberOf", "userAccountControl",
}

func (d *ldapDirectory) Authenticate(username, password string) (User,
	error) {
	if username == "" || password == "" {
		return User{}, fmt.Errorf("아이디와 비밀번호가 필요합니다")
	}

	// ── 1. 서비스 계정으로 붙어 사람을 찾는다 ──
	svc, err := d.dial()
	if err != nil {
		return User{}, fmt.Errorf("AD 에 붙지 못했습니다: %w", err)
	}
	defer svc.Close()
	if err := svc.Bind(d.cfg.BindDN, d.cfg.BindPassword); err != nil {
		// 이 오류가 나면 **모든 사용자**의 로그인이 멈춘다.
		// 서비스 계정의 비밀번호가 틀렸거나 잠긴 것이다(3부 5장).
		return User{}, fmt.Errorf("서비스 계정 바인드 실패: %w", err)
	}

	// 필터를 **나무로 지어** 문자열로 만든다.
	//
	// 사용자가 친 값을 문자열에 그대로 끼워 넣으면 안 된다 —
	// `*)(objectClass=*` 한 줄로 필터의 뜻이 바뀐다(3부 6장 퀴즈).
	// String() 이 RFC 4515 §3 대로 감싸 준다.
	f := &proto.And{Subs: []proto.Filter{
		&proto.Equal{Attr: "objectClass", Value: "user"},
		&proto.Equal{Attr: d.cfg.UsernameAttr, Value: username},
	}}
	found, err := svc.Search(d.cfg.BaseDN, proto.ScopeWholeSubtree,
		f.String(), wantAttrs)
	if err != nil {
		return User{}, fmt.Errorf("검색 실패: %w", err)
	}
	if len(found) == 0 {
		// 없는 사람이라고 말해 주지 않는다.
		// 알려 주면 아이디 목록을 만들 수 있다.
		return User{}, fmt.Errorf("아이디나 비밀번호가 맞지 않습니다")
	}
	if len(found) > 1 {
		// 여럿이 걸리면 누구인지 정할 수 없다. 통과시키면 안 된다.
		return User{}, fmt.Errorf("%q 로 %d명이 걸렸습니다 — "+
			"아이디 속성을 다시 볼 것", username, len(found))
	}
	e := found[0]

	// ── 2. 그 사람의 DN 으로 **다른 연결**에서 비밀번호를 확인한다 ──
	as, err := d.dial()
	if err != nil {
		return User{}, fmt.Errorf("AD 에 붙지 못했습니다: %w", err)
	}
	defer as.Close()
	if err := as.Bind(e.DN, password); err != nil {
		// 여기 담긴 진단 문구에 AD 의 data 코드가 들어 있다(3부 5장).
		return User{}, err
	}

	return User{
		DN:       e.DN,
		Username: e.First(d.cfg.UsernameAttr),
		Email:    e.First("mail"),
		Name:     pickName(e),
		Groups:   groupNames(e.Values("memberOf")),
	}, nil
}

// pickName 은 화면에 보여 줄 이름을 고른다. displayName 이 있으면 그것,
// 없으면 cn. 7부의 매퍼가 이 선택을 설정 칸으로 내준다.
func pickName(e client.Entry) string {
	if v := e.First("displayName"); v != "" {
		return v
	}
	return e.First("cn")
}

// groupNames 는 그룹 DN 목록에서 이름만 뽑는다.
//
//	CN=lunch-users,OU=Groups,DC=ad,…  →  lunch-users
//
// 토큰에 DN 을 통째로 싣지 않는 이유는 두 가지다. 길고(9부의 토큰 크기
// 문제), 앱이 볼 필요가 없다. Keycloak 의 group-ldap-mapper 에도
// "전체 경로를 쓸 것인가" 스위치가 있고, 대개 끈다(7·9부).
func groupNames(dns []string) []string {
	var out []string
	for _, dn := range dns {
		first := dn
		if i := strings.Index(dn, ","); i >= 0 {
			first = dn[:i]
		}
		if i := strings.Index(first, "="); i >= 0 {
			first = first[i+1:]
		}
		if first != "" {
			out = append(out, first)
		}
	}
	return out
}
