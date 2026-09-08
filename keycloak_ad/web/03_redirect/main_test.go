package main

import (
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
)

func TestChainStepsAndCodes(t *testing.T) {
	cases := []struct {
		path     string
		handler  func(http.ResponseWriter, *http.Request)
		wantCode int
		wantLoc  string
	}{
		{"/start", handleStart, http.StatusFound, "/step2"},
		{"/step2", handleStep2, http.StatusFound, "/step3"},
	}
	for _, c := range cases {
		w := httptest.NewRecorder()
		c.handler(w, httptest.NewRequest("GET", c.path, nil))
		if w.Code != c.wantCode {
			t.Errorf("%s 상태=%d 원하는 것 %d",
				c.path, w.Code, c.wantCode)
		}
		if loc := w.Header().Get("Location"); loc != c.wantLoc {
			t.Errorf("%s Location=%q 원하는 것 %q",
				c.path, loc, c.wantLoc)
		}
	}
}

// 사슬의 끝은 더 이상 옮기지 않는다. 이게 없으면 영원히 돈다.
func TestChainEndIs200(t *testing.T) {
	w := httptest.NewRecorder()
	handleStep3(w, httptest.NewRequest("GET", "/step3", nil))
	if w.Code != http.StatusOK {
		t.Errorf("상태 = %d, 원하는 것 200", w.Code)
	}
	if loc := w.Header().Get("Location"); loc != "" {
		t.Errorf("끝에는 Location 이 없어야 한다: %q", loc)
	}
}

func TestRedirectCode(t *testing.T) {
	cases := []struct {
		in   string
		want int
		ok   bool
	}{
		{"301", 301, true},
		{"302", 302, true},
		{"303", 303, true},
		{"307", 307, true},
		{"308", 308, true},
		{"", 302, true},   // 기본값
		{"200", 0, false}, // 옮기라는 뜻이 아니다
		{"304", 0, false}, // 3xx 지만 옮기라는 뜻이 아니다
		{"999", 0, false}, //
		{"삼공이", 0, false}, // 숫자가 아니다
		{"-302", 0, false},
	}
	for _, c := range cases {
		got, ok := redirectCode(c.in)
		if ok != c.ok || (ok && got != c.want) {
			t.Errorf("redirectCode(%q) = %d,%v — 원하는 것 %d,%v",
				c.in, got, ok, c.want, c.ok)
		}
	}
}

func TestHandleMethodUsesGivenCode(t *testing.T) {
	w := httptest.NewRecorder()
	r := httptest.NewRequest("POST", "/method?code=307", nil)
	handleMethod(w, r)
	if w.Code != 307 {
		t.Errorf("상태 = %d, 원하는 것 307", w.Code)
	}
	if loc := w.Header().Get("Location"); loc != "/landed" {
		t.Errorf("Location = %q, 원하는 것 /landed", loc)
	}
}

func TestHandleMethodRejectsBadCode(t *testing.T) {
	w := httptest.NewRecorder()
	handleMethod(w, httptest.NewRequest("GET", "/method?code=200", nil))
	if w.Code != http.StatusBadRequest {
		t.Errorf("상태 = %d, 원하는 것 400", w.Code)
	}
}

// 도착지는 "무슨 방법으로 왔는지" 를 그대로 말한다. 307 과 303 의
// 차이를 눈으로 보는 자리가 바로 여기다.
func TestHandleLandedReportsMethod(t *testing.T) {
	w := httptest.NewRecorder()
	handleLanded(w, httptest.NewRequest("POST", "/landed",
		strings.NewReader("a=1")))
	body := w.Body.String()
	if !strings.Contains(body, "POST") {
		t.Errorf("도착지가 방법을 말하지 않는다: %q", body)
	}
}

// 고리는 유한해야 캡처를 뜰 수 있다. n 을 세어 열 번째에 멈춘다.
func TestLoopCountsAndStops(t *testing.T) {
	w := httptest.NewRecorder()
	handleLoop(w, httptest.NewRequest("GET", "/loop?n=0", nil))
	if w.Code != http.StatusFound {
		t.Fatalf("상태 = %d, 원하는 것 302", w.Code)
	}
	if loc := w.Header().Get("Location"); loc != "/loop?n=1" {
		t.Errorf("Location = %q, 원하는 것 /loop?n=1", loc)
	}

	w = httptest.NewRecorder()
	handleLoop(w, httptest.NewRequest("GET", "/loop?n=10", nil))
	if w.Code != http.StatusOK {
		t.Errorf("열 번째 상태 = %d, 원하는 것 200", w.Code)
	}
}

// Location 은 상대 주소여도 된다(RFC 7231 §7.1.2). 브라우저가 지금
// 주소를 기준으로 붙여 준다. 절대 주소를 요구하던 옛 규정(RFC 2616)이
// 바뀐 자리다.
func TestRelativeLocationIsKeptRelative(t *testing.T) {
	w := httptest.NewRecorder()
	handleStart(w, httptest.NewRequest("GET", "/start", nil))
	loc := w.Header().Get("Location")
	if strings.HasPrefix(loc, "http") {
		t.Errorf("절대 주소다: %q — 이 덱은 상대 주소를 쓴다", loc)
	}
}
