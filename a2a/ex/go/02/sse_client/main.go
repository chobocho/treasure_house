// SSE 클라이언트 — net/http 와 bufio 만으로. 줄을 읽다가 빈 줄을
// 만나면 모아 둔 data 를 이벤트 하나로 내보낸다.
package main

import (
	"bufio"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"iter"
	"net/http"
	"strings"
)

// region: parse
// 본문 → 이벤트의 data 문자열들. 빈 줄이 이벤트의 끝이다.
func sseEvents(body io.Reader) iter.Seq[string] {
	return func(yield func(string) bool) {
		sc := bufio.NewScanner(body) // 줄 끝의 \r\n·\n 을 떼 준다
		var data []string
		for sc.Scan() {
			line := sc.Text()
			switch {
			case line == "":
				if len(data) > 0 && !yield(strings.Join(data, "\n")) {
					return
				}
				data = nil
			case strings.HasPrefix(line, ":"): // 주석 — 버린다
			default:
				field, value, _ := strings.Cut(line, ":")
				if field == "data" {
					data = append(data, strings.TrimPrefix(value, " "))
				}
			}
		}
		// 빈 줄 없이 끝난 조각은 이벤트가 아니다 — 버린다
	}
}

// endregion

// region: main
func main() {
	url := flag.String("url", "", "서버 주소")
	flag.Parse()
	body := `{"nights":1,"headcount":30,"vegetarians":2}`
	req, _ := http.NewRequest("POST", *url, strings.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Accept", "text/event-stream")
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		panic(err)
	}
	defer resp.Body.Close()
	n := 0
	for data := range sseEvents(resp.Body) {
		var ev map[string]any
		json.Unmarshal([]byte(data), &ev)
		n++
		if slot, ok := ev["slot"]; ok {
			fmt.Printf("이벤트 %d: %s %s / 채식 %s\n",
				n, slot, ev["regular"], ev["vegetarian"])
		} else { // any 로 읽은 수는 float64 다(2장)
			fmt.Printf("이벤트 %d: 합계 %.0f원\n", n, ev["total"])
		}
	}
	fmt.Printf("스트림 끝 — 이벤트 %d개\n", n)
}

// endregion
//@ norun
