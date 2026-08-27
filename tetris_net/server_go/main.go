package main

// main.go — 서버 실행 파일. 외부 의존성이 0이라 `go build` 하나로 단일 바이너리가 나온다.
//
//	go build -o tetris-server .
//	./tetris-server -addr :8787 -dir ../web
//
// 하는 일은 셋뿐이다: /ws 로 웹소켓을 받고, -dir 이 있으면 정적 파일을 내주고,
// /rooms 로 지금 열려 있는 방을 보여 준다.

import (
	"context"
	"encoding/json"
	"flag"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"
)

func main() {
	addr := flag.String("addr", ":8787", "듣는 주소")
	dir := flag.String("dir", "", "같이 내줄 정적 파일 디렉터리 (비우면 웹소켓만)")
	flag.Parse()

	hub := NewHub()
	mux := http.NewServeMux()
	mux.HandleFunc("/ws", hub.ServeWS)
	mux.HandleFunc("/rooms", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json; charset=utf-8")
		json.NewEncoder(w).Encode(map[string]any{"v": ProtoVersion, "rooms": hub.Stats()})
	})
	mux.HandleFunc("/healthz", func(w http.ResponseWriter, r *http.Request) { w.Write([]byte("ok")) })
	if *dir != "" {
		mux.Handle("/", http.FileServer(http.Dir(*dir)))
	} else {
		mux.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
			w.Header().Set("Content-Type", "text/plain; charset=utf-8")
			w.Write([]byte("테트리스 8인 대전 서버 v3 — 웹소켓은 /ws\n"))
		})
	}

	srv := &http.Server{
		Addr:    *addr,
		Handler: mux,
		// 웹소켓은 업그레이드 뒤 오래 살아 있어야 하므로 읽기/쓰기 전체 타임아웃을 걸면 안 된다.
		// 헤더 타임아웃만 걸어 슬로로리스류를 막는다.
		ReadHeaderTimeout: 10 * time.Second,
	}

	go func() {
		log.Printf("듣는 중: %s (프로토콜 v%d)", *addr, ProtoVersion)
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("서버가 죽었다: %v", err)
		}
	}()

	// Ctrl-C 를 받으면 새 연결만 막고 5초 기다렸다 내려간다.
	// 진행 중인 판이 있으면 그 판은 그대로 끝난다.
	stop := make(chan os.Signal, 1)
	signal.Notify(stop, os.Interrupt, syscall.SIGTERM)
	<-stop
	log.Println("종료 신호를 받았다 — 5초 안에 정리한다")
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	if err := srv.Shutdown(ctx); err != nil {
		log.Printf("정리 중 오류: %v", err)
	}
}
