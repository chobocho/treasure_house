// Package deploy 는 SDK 처리기를 감싸는 배포용 HTTP 미들웨어 둘 —
// 카드 캐시 머리글과 본문 한도.
package deploy

import (
	"crypto/sha256"
	"fmt"
	"net/http"
	"net/http/httptest"
)

// region: cache
// CardCache 는 카드 처리기를 감싸 ETag·Cache-Control 을 달고, 받아
// 둔 ETag 이 If-None-Match 로 오면 본문 없이 304 를 돌려준다
// (§8.6.1). ETag 은 본문의 해시라 카드가 바뀌면 함께 바뀐다.
func CardCache(maxAge int, next http.Handler) http.Handler {
	return http.HandlerFunc(func(
		w http.ResponseWriter, r *http.Request,
	) {
		got := httptest.NewRecorder() // SDK 의 응답을 먼저 받아 둔다
		next.ServeHTTP(got, r)
		body := got.Body.Bytes()
		sum := sha256.Sum256(body)
		tag := fmt.Sprintf(`W/"%x"`, sum[:8])
		h := w.Header()
		for k, v := range got.Header() {
			h[k] = v
		}
		if got.Code == http.StatusOK {
			h.Set("ETag", tag)
			h.Set("Cache-Control",
				fmt.Sprintf("public, max-age=%d", maxAge))
			if r.Header.Get("If-None-Match") == tag {
				w.WriteHeader(http.StatusNotModified)
				return
			}
		}
		w.WriteHeader(got.Code)
		_, _ = w.Write(body)
	})
}

// endregion

// region: limit
// Limit 은 요청 본문을 n 바이트로 묶는다. 길이를 밝힌 요청은 읽기 전에
// 413 으로 돌려보내고, 밝히지 않은 요청(chunked)은 n 바이트에서 읽기를
// 끊는다 — 그때는 SDK 의 JSON 해독이 오류를 받는다.
func Limit(n int64, next http.Handler) http.Handler {
	return http.HandlerFunc(func(
		w http.ResponseWriter, r *http.Request,
	) {
		if r.ContentLength > n {
			w.Header().Set("Content-Type", "application/json")
			w.WriteHeader(http.StatusRequestEntityTooLarge)
			_, _ = w.Write([]byte(tooLarge))
			return
		}
		r.Body = http.MaxBytesReader(w, r.Body, n)
		next.ServeHTTP(w, r)
	})
}

// 스펙에 크기 초과 오류는 없다 — 파이썬처럼 Invalid Request 를 싣는다
const tooLarge = `{"jsonrpc": "2.0", "id": null, "error": ` +
	`{"code": -32600, "message": "요청 본문이 너무 큽니다"}}`

	// endregion
