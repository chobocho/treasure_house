// 슬라이드 p3-v12-encoding — TextMarshaler 로 JSON·XML, Go 1.2
package main

import (
	"encoding"
	"encoding/json"
	"encoding/xml"
	"fmt"
	"strings"
)

type Level int

var names = []string{"debug", "info", "warn"}

func (l Level) MarshalText() ([]byte, error) {
	return []byte(names[l]), nil
}

func (l *Level) UnmarshalText(b []byte) error {
	for i, n := range names {
		if n == strings.ToLower(string(b)) {
			*l = Level(i)
			return nil
		}
	}
	return fmt.Errorf("unknown level %q", b)
}

var _ encoding.TextMarshaler = Level(0) // compile-time check
type Config struct {
	Level Level `json:"level" xml:"level,attr"`
}

func main() {
	j, _ := json.Marshal(Config{Level: 2})
	x, _ := xml.Marshal(Config{Level: 1})
	fmt.Println(string(j))
	fmt.Println(string(x))

	var c Config
	err := json.Unmarshal([]byte(`{"level":"DEBUG"}`), &c)
	fmt.Println(c.Level, err)
}
