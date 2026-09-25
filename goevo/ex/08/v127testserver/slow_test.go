// 슬라이드 p8-v127-testserver — 가짜 네트워크와 synctest.Sleep, Go 1.27
package slow

import (
	"io"
	"net/http"
	"net/http/httptest"
	"testing"
	"testing/synctest"
	"time"
)

func TestSlow(t *testing.T) {
	synctest.Test(t, func(t *testing.T) {
		h := http.HandlerFunc(Handler)
		srv := httptest.NewTestServer(t, h)
		start := time.Now()
		res, err := srv.Client().Get(srv.URL)
		if err != nil {
			t.Fatal(err)
		}
		body, _ := io.ReadAll(res.Body)
		res.Body.Close()
		synctest.Sleep(time.Minute) // sleep, then wait
		t.Logf("%s after %v", body, time.Since(start))
	})
}
