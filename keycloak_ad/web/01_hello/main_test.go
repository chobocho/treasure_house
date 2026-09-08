package main

import (
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
)

// 요청을 글로 옮기는 부분이 이 프로그램의 전부다. 그래서 여기만
// 시험한다. 서버를 진짜로 띄우지 않고도 확인할 수 있는 것은 띄우지 않고
// 확인한다 — 포트가 겹치는 순간 시험은 기계가 바쁠 때마다 다르게
// 실패한다.
func TestRequestDumpFirstLine(t *testing.T) {
	r := httptest.NewRequest("GET", "/echo?a=1", nil)
	r.Proto = "HTTP/1.1"
	got := requestDump(r)
	want := "GET /echo?a=1 HTTP/1.1"
	if first := strings.SplitN(got, "\n", 2)[0]; first != want {
		t.Errorf("첫 줄 = %q, 원하는 것 %q", first, want)
	}
}

// 헤더는 지도(map)라 Go 가 돌 때마다 순서를 바꾼다. 그대로 찍으면
// 캡처가 매번 달라져 "두 번 돌려 같은지" 검사를 통과할 수 없다. 그래서
// 정렬한다.
func TestRequestDumpHeadersSorted(t *testing.T) {
	r := httptest.NewRequest("GET", "/", nil)
	r.Header.Set("Zeta", "z")
	r.Header.Set("Alpha", "a")
	r.Header.Set("Mike", "m")
	got := requestDump(r)
	ia := strings.Index(got, "Alpha:")
	im := strings.Index(got, "Mike:")
	iz := strings.Index(got, "Zeta:")
	if ia < 0 || im < 0 || iz < 0 {
		t.Fatalf("헤더가 빠졌다:\n%s", got)
	}
	if !(ia < im && im < iz) {
		t.Errorf("헤더가 가나다순이 아니다:\n%s", got)
	}
}

// 값이 여럿인 헤더(Accept 같은 것)는 줄을 나눠 전부 보여 준다.
func TestRequestDumpRepeatedHeader(t *testing.T) {
	r := httptest.NewRequest("GET", "/", nil)
	r.Header.Add("X-Try", "one")
	r.Header.Add("X-Try", "two")
	got := requestDump(r)
	if strings.Count(got, "X-Try:") != 2 {
		t.Errorf("같은 이름의 헤더 두 줄이 나와야 한다:\n%s", got)
	}
}

// Host 는 헤더인데도 Go 가 r.Header 에서 빼서 r.Host 에 따로 담는다.
// 그대로 두면 캡처에서 Host 줄이 통째로 사라진다 — 초심자가 가장
// 헷갈리는 자리다.
func TestRequestDumpIncludesHost(t *testing.T) {
	r := httptest.NewRequest("GET", "/", nil)
	r.Host = "lunch.campus.example"
	got := requestDump(r)
	if !strings.Contains(got, "Host: lunch.campus.example") {
		t.Errorf("Host 줄이 없다:\n%s", got)
	}
}

func TestHandleEchoIsPlainText(t *testing.T) {
	r := httptest.NewRequest("GET", "/echo", nil)
	w := httptest.NewRecorder()
	handleEcho(w, r)
	res := w.Result()
	if res.StatusCode != http.StatusOK {
		t.Errorf("상태 = %d, 원하는 것 200", res.StatusCode)
	}
	ct := res.Header.Get("Content-Type")
	if !strings.HasPrefix(ct, "text/plain") {
		t.Errorf("Content-Type = %q, text/plain 이어야 한다", ct)
	}
}

func TestHandleHelloOnRoot(t *testing.T) {
	r := httptest.NewRequest("GET", "/", nil)
	w := httptest.NewRecorder()
	handleHello(w, r)
	if w.Result().StatusCode != http.StatusOK {
		t.Errorf("/ 는 200 이어야 한다, 받은 것 %d", w.Code)
	}
	if !strings.Contains(w.Body.String(), "학식 예약") {
		t.Errorf("본문에 서비스 이름이 없다: %q", w.Body.String())
	}
}

// "/" 로 등록한 핸들러는 등록되지 않은 모든 주소도 받는다. 그래서 직접
// 404 를 내야 한다. 이걸 빼먹으면 오타 주소가 조용히 첫 페이지를 보여
// 준다.
func TestHandleHelloUnknownPathIs404(t *testing.T) {
	r := httptest.NewRequest("GET", "/없는주소", nil)
	w := httptest.NewRecorder()
	handleHello(w, r)
	if w.Code != http.StatusNotFound {
		t.Errorf("모르는 주소 = %d, 원하는 것 404", w.Code)
	}
}
