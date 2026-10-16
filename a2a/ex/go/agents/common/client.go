package common

import (
	"net/http"
	"time"
)

// HTTPClient 는 클라이언트 쪽(ask·기획)이 쓰는 HTTP 클라이언트다.
// token 이 있으면 매 요청에 Authorization: Bearer 를 붙인다.
// 전체 시간 제한(Timeout)은 걸지 않는다 — 스트림(SSE)은 오래
// 열려 있으므로, 응답 머리가 올 때까지만 30초를 기다린다.
func HTTPClient(token string) *http.Client {
	base := http.DefaultTransport.(*http.Transport).Clone()
	base.ResponseHeaderTimeout = 30 * time.Second
	return &http.Client{Transport: bearer{base, token}}
}

type bearer struct {
	next  http.RoundTripper
	token string
}

func (b bearer) RoundTrip(r *http.Request) (*http.Response, error) {
	if b.token != "" {
		r = r.Clone(r.Context())
		r.Header.Set("Authorization", "Bearer "+b.token)
	}
	return b.next.RoundTrip(r)
}
