// 슬라이드 p5-v115-tzdata — 시간대 데이터를 실행 파일에, Go 1.15
package main

import (
	"fmt"
	"time"
	_ "time/tzdata" // embeds the database (about 800 KB per the notes)
)

func main() {
	t := time.Date(2020, 8, 11, 12, 0, 0, 0, time.UTC)
	zones := []string{"Asia/Seoul", "America/New_York", "Europe/Berlin"}
	for _, name := range zones {
		loc, err := time.LoadLocation(name)
		if err != nil {
			fmt.Println(name, err)
			continue
		}
		fmt.Println(t.In(loc).Format("2006-01-02 15:04 MST"), name)
	}
}
