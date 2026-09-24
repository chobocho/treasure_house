// 슬라이드 p4-v16-template — 공백 다듬기와 block, Go 1.6
package main

import (
	"os"
	"text/template"
)

const base = `{{define "page"}}[{{block "body" .}}default{{end}}]` +
	`{{end}}`

func main() {
	// "-" trims the white space on that side of the action.
	src := "{{23 -}}\n   <\n{{- 45}}\n"
	trim := template.Must(template.New("t").Parse(src))
	trim.Execute(os.Stdout, nil)

	page := template.Must(template.New("base").Parse(base))
	page.ExecuteTemplate(os.Stdout, "page", nil)
	os.Stdout.WriteString("\n")

	// Redefine the block in a clone: only "body" changes.
	custom := template.Must(page.Clone())
	template.Must(custom.Parse(`{{define "body"}}custom{{end}}`))
	custom.ExecuteTemplate(os.Stdout, "page", nil)
	os.Stdout.WriteString("\n")
}
