// 슬라이드 p5-v111-small — 템플릿 대입·숫자 시간대·캐시 위치, Go 1.11
package main

import (
	"fmt"
	"os"
	"text/template"
	"time"
)

const tmpl = `{{$v := "init"}}{{if true}}{{$v = "changed"}}{{end}}
v: {{$v}}
`

func main() {
	t := template.Must(template.New("t").Parse(tmpl))
	t.Execute(os.Stdout, nil)

	layout := "2006-01-02 15:04 MST"
	ts, err := time.Parse(layout, "2018-08-24 09:00 +03")
	fmt.Println(ts, err)

	dir, err := os.UserCacheDir()
	fmt.Println(dir, err)
}
