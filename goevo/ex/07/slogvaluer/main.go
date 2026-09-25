// 슬라이드 p7-v121-slogvaluer — LogValuer·레벨·log 와의 다리, Go 1.21
package main

import (
	"log"
	"log/slog"
	"os"
)

type Token string

// LogValue keeps secrets out of every log line.
func (Token) LogValue() slog.Value {
	return slog.StringValue("REDACTED")
}

type User struct {
	ID   int
	Name string
}

func (u User) LogValue() slog.Value {
	return slog.GroupValue(
		slog.Int("id", u.ID), slog.String("name", u.Name))
}

func main() {
	var level slog.LevelVar // changeable at run time
	h := slog.NewTextHandler(os.Stdout, &slog.HandlerOptions{
		Level: &level,
		ReplaceAttr: func(g []string, a slog.Attr) slog.Attr {
			if len(g) == 0 && a.Key == slog.TimeKey {
				return slog.Attr{}
			}
			return a
		},
	})
	slog.SetDefault(slog.New(h))

	slog.Info("login", "user", User{7, "ana"}, "token", Token("s3cret"))
	slog.Debug("hidden")
	level.Set(slog.LevelDebug)
	slog.Debug("now visible")
	log.Printf("old log.Printf goes through slog: %d", 1)
}
