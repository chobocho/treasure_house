package mygit

// 작업 트리 (SPEC.md §8) — 경로 따옴표, 훑기, status.

import (
	"fmt"
	"strings"
)

// \a \b \t \n \v \f \r 와 따옴표·역슬래시는 두 글자로 쓴다
var short = map[byte]byte{7: 'a', 8: 'b', 9: 't', 10: 'n', 11: 'v',
	12: 'f', 13: 'r', 34: '"', 92: '\\'}

// QuotePath 는 경로 → git 이 사람에게 찍는 꼴 (core.quotePath=true).
// 제어 문자·DEL·따옴표·역슬래시·0x80 이상 바이트가 하나라도 있으면
// 전체를 따옴표로 감싸고 C 식으로 쓴다(8진 세 자리). space 는 status
// 의 규칙 — 공백만 있어도 감싼다. O(경로 길이).
func QuotePath(path string, space bool) string {
	need := space && strings.IndexByte(path, ' ') >= 0
	var b strings.Builder
	for i := 0; i < len(path); i++ {
		c := path[i]
		if s, ok := short[c]; ok {
			b.WriteByte('\\')
			b.WriteByte(s)
			need = true
		} else if c < 32 || c >= 127 {
			fmt.Fprintf(&b, "\\%03o", c)
			need = true
		} else {
			b.WriteByte(c)
		}
	}
	if need {
		return "\"" + b.String() + "\""
	}
	return b.String()
}
