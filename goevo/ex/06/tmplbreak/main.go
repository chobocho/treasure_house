// 슬라이드 p6-v118-template — {{break}}·{{continue}}, Go 1.18
package main

import (
	"os"
	"text/template"
)

const src = `{{range .}}{{if eq . "skip"}}{{continue}}{{end -}}
{{if eq . "stop"}}{{break}}{{end}}[{{.}}] {{end}}
{{if and false (fail)}}never{{else}}and stopped early{{end}}
`

func main() {
	funcs := template.FuncMap{
		"fail": func() (string, error) { panic("evaluated") },
	}
	t := template.Must(template.New("t").Funcs(funcs).Parse(src))
	words := []string{"a", "skip", "b", "stop", "c"}
	if err := t.Execute(os.Stdout, words); err != nil {
		panic(err)
	}
}
