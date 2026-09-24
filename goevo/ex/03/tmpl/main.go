// 슬라이드 p3-v12-template — 템플릿의 비교 함수와 else if, Go 1.2
package main

import (
	"os"
	"text/template"
)

const src = `{{range .}}{{.}}: ` +
	`{{if eq . 1 2 3}}small{{else if lt . 10}}medium{{else}}large{{end}}
{{end}}`

func main() {
	t := template.Must(template.New("size").Parse(src))
	if err := t.Execute(os.Stdout, []int{2, 7, 12}); err != nil {
		panic(err)
	}
}
