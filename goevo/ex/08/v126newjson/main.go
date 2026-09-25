// 슬라이드 p8-v126-newjson — new(expr) 로 선택적 필드 채우기, Go 1.26
package main

import (
	"encoding/json"
	"fmt"
	"time"
)

type Person struct {
	Name string `json:"name"`
	Age  *int   `json:"age"` // age if known; nil otherwise
}

// newInt is the helper everyone used to write before Go 1.26.
func newInt(x int) *int { return &x }

func years(from, to time.Time) int {
	n := to.Year() - from.Year()
	if to.YearDay() < from.YearDay() {
		n--
	}
	return n
}

func main() {
	today := time.Date(2026, 2, 10, 0, 0, 0, 0, time.UTC)
	born := time.Date(2009, 11, 10, 0, 0, 0, 0, time.UTC)

	for _, p := range []Person{
		{Name: "unknown"},
		{Name: "helper", Age: newInt(16)},
		{Name: "go1.26", Age: new(years(born, today))},
	} {
		b, err := json.Marshal(p)
		fmt.Println(string(b), err)
	}
}
