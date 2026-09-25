// 슬라이드 p7-v123-small2 — else with·Pattern·ParseCookie, Go 1.23
package main

import (
	"fmt"
	"net/http"
	"net/http/httptest"
	"os"
	"text/template"
)

const tpl = `{{with .Nick}}nick {{.}}{{else with .Name}}name {{.}}` +
	`{{else}}anonymous{{end}}` + "\n"

func showPattern(_ http.ResponseWriter, r *http.Request) {
	fmt.Println("matched pattern:", r.Pattern)
}

func main() {
	t := template.Must(template.New("t").Parse(tpl))
	t.Execute(os.Stdout, map[string]string{"Name": "Ana"})
	t.Execute(os.Stdout, map[string]string{})

	mux := http.NewServeMux()
	mux.HandleFunc("GET /u/{id}", showPattern)
	req := httptest.NewRequest("GET", "/u/1", nil)
	mux.ServeHTTP(httptest.NewRecorder(), req)

	cookies, _ := http.ParseCookie(`a=1; b="two"; a=3`)
	for _, c := range cookies {
		fmt.Print(c.Name, "=", c.Value, " quoted=", c.Quoted, "; ")
	}
	fmt.Println()
}
