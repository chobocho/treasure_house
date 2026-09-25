// 슬라이드 p7-v124-small2 — 템플릿 range·DiscardHandler, Go 1.24
package main

import (
	"log/slog"
	"maps"
	"os"
	"text/template"
)

func main() {
	t := template.Must(template.New("t").Parse(
		"{{range 3}}{{.}} {{end}}| " +
			"{{range $k, $v := .}}{{$k}}={{$v}} {{end}}\n"))
	m := map[string]int{"a": 1}
	t.Execute(os.Stdout, maps.All(m)) // a func iterator in a template

	quiet := slog.New(slog.DiscardHandler)
	quiet.Error("nobody sees this")
}
