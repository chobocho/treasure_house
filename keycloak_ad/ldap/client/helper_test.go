package client

import (
	"errors"
	"io"
	"testing"

	"treasure/keycloak_ad/ldap/fakead"
)

// spawnFakeAD 는 3부에서 만든 가짜 AD 를 시험용으로 하나 띄운다.
//
// 흉내 낸 서버가 아니라 **진짜 그 서버**에 대고 시험하는 것이 요점이다.
// 우리 생각대로 도는지가 아니라 실제로 통하는지를 봐야 하기 때문이다.
// 포트는 0 을 줘서 운영체제가 남는 것을 고르게 한다 — 시험을 여러 개
// 나란히 돌려도 안 겹친다.
func spawnFakeAD(t *testing.T) (addr string, stop func()) {
	t.Helper()
	d, err := fakead.LoadLDIFFile("../../data/campus.ldif")
	if err != nil {
		t.Fatalf("LDIF: %v", err)
	}
	srv := fakead.NewServer(d, io.Discard)
	if err := srv.ListenPlain("127.0.0.1:0"); err != nil {
		t.Fatalf("띄우지 못했다: %v", err)
	}
	return srv.Addr(), srv.Close
}

// asBindError 는 errors.As 를 시험에서 짧게 쓰려고 감싼 것이다.
func asBindError(err error, target **BindError) bool {
	return errors.As(err, target)
}
