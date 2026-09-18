package mygit

// 시험 도우미 — golden/ 을 읽고 재료를 바이트로 만든다(SPEC §2.1).
// golden 은 진짜 git 이 만든 기준 바이트다. 시험은 git 을 부르지
// 않고 이 파일들만 읽는다.

import (
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"testing"
)

const goldenDir = "../golden"

func gread(t testing.TB, parts ...string) []byte {
	t.Helper()
	b, err := os.ReadFile(filepath.Join(append([]string{goldenDir},
		parts...)...))
	if err != nil {
		t.Fatal(err)
	}
	return b
}

// gtsv 는 주석(#)과 머리 줄을 뺀 행들을 칸 이름 → 값으로 돌려준다.
func gtsv(t testing.TB, parts ...string) []map[string]string {
	var head []string
	var rows []map[string]string
	for _, line := range strings.Split(string(gread(t, parts...)),
		"\n") {
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		cols := strings.Split(line, "\t")
		if head == nil {
			head = cols
			continue
		}
		row := map[string]string{}
		for i, h := range head {
			if i < len(cols) {
				row[h] = cols[i]
			}
		}
		rows = append(rows, row)
	}
	return rows
}

// unescape 는 text: 재료의 \n \t \\ \" \xHH 를 푼다.
func unescape(s string) []byte {
	var out []byte
	for i := 0; i < len(s); i++ {
		c := s[i]
		if c != '\\' || i+1 >= len(s) {
			out = append(out, c)
			continue
		}
		n := s[i+1]
		switch n {
		case 'x':
			v, _ := strconv.ParseUint(s[i+2:i+4], 16, 8)
			out = append(out, byte(v))
			i += 3
		case 'n':
			out = append(out, '\n')
			i++
		case 't':
			out = append(out, '\t')
			i++
		default:
			out = append(out, n)
			i++
		}
	}
	return out
}

// makeRecipe 는 재료 한 줄을 바이트로 만든다(SPEC §2.1 · §16.4).
func makeRecipe(t testing.TB, r string) []byte {
	kind, arg, _ := strings.Cut(r, ":")
	switch kind {
	case "empty":
		return []byte{}
	case "text":
		return unescape(arg)
	case "repeat":
		b, n, _ := strings.Cut(arg, ":")
		v, _ := strconv.ParseUint(b, 16, 8)
		k, _ := strconv.Atoi(n)
		return []byte(strings.Repeat(string([]byte{byte(v)}), k))
	case "counter":
		k, _ := strconv.Atoi(arg)
		out := make([]byte, k)
		for i := range out {
			out[i] = byte(i % 251)
		}
		return out
	case "seq":
		a, b, _ := strings.Cut(arg, ":")
		x, _ := strconv.Atoi(a)
		y, _ := strconv.Atoi(b)
		var sb strings.Builder
		for i := x; i <= y; i++ {
			sb.WriteString(strconv.Itoa(i) + "\n")
		}
		return []byte(sb.String())
	case "golden":
		return gread(t, arg)
	}
	t.Fatalf("모르는 재료: %s", r)
	return nil
}
