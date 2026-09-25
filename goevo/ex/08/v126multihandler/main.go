// 슬라이드 p8-v126-multihandler — slog.NewMultiHandler, Go 1.26
package main

import (
	"log/slog"
	"os"
)

func main() {
	noTime := func(groups []string, a slog.Attr) slog.Attr {
		if a.Key == slog.TimeKey && len(groups) == 0 {
			return slog.Attr{} // drop the time for a stable output
		}
		return a
	}
	text := slog.NewTextHandler(os.Stdout, &slog.HandlerOptions{
		Level: slog.LevelDebug, ReplaceAttr: noTime,
	})
	json := slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{
		Level: slog.LevelWarn, ReplaceAttr: noTime,
	})

	// One logger, two handlers. Each handler keeps its own level.
	log := slog.New(slog.NewMultiHandler(text, json)).
		With("release", "go1.26")
	log.Debug("only text sees this")
	log.Warn("both see this", "n", 2)
}
