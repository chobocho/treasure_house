// 슬라이드 p7-v121-slog — 구조화 로깅 log/slog, Go 1.21
package main

import (
	"log/slog"
	"os"
)

// dropTime removes the time attribute so the output is reproducible.
func dropTime(groups []string, a slog.Attr) slog.Attr {
	if len(groups) == 0 && a.Key == slog.TimeKey {
		return slog.Attr{}
	}
	return a
}

func main() {
	opts := &slog.HandlerOptions{ReplaceAttr: dropTime}
	text := slog.New(slog.NewTextHandler(os.Stdout, opts))
	text.Info("hello, world", "user", "gopher", "n", 3)
	text.Debug("not shown: below the default level Info")

	req := text.With("req", 42) // formatted once, reused
	req.Warn("slow", slog.Group("db", "table", "users", "ms", 120))

	js := slog.New(slog.NewJSONHandler(os.Stdout, opts))
	js.Error("failed", "err", os.ErrNotExist, "retry", true)
}
