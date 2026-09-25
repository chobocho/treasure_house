// 슬라이드 p7-v124-omitzero — encoding/json 의 omitzero, Go 1.24
package main

import (
	"encoding/json"
	"fmt"
	"time"
)

type Money struct{ Cents int64 }

func (m Money) IsZero() bool { return m.Cents == 0 }

type Event struct {
	Name    string    `json:"name"`
	Old     time.Time `json:"old,omitempty"` // struct: never "empty"
	New     time.Time `json:"new,omitzero"`
	Tags    []string  `json:"tags,omitempty"` // nil and [] both omitted
	TagsZ   []string  `json:"tagsz,omitzero"` // only nil omitted
	Price   Money     `json:"price,omitzero"` // uses IsZero
	Retries int       `json:"retries,omitzero"`
}

func main() {
	b, _ := json.Marshal(Event{Name: "launch", TagsZ: []string{}})
	fmt.Println(string(b))
}
