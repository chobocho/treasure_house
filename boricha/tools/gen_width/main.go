// gen_width — width/widthdata.txt 를 읽어 width/table.go 를 만든다.
//
// 왜 표를 코드로 굽는가. 프로그램이 돌 때마다 11 KB 짜리 텍스트를 읽고 파싱하는 것은
// 낭비이고, 무엇보다 그 파일을 배포에 딸려 보내야 한다. 우리 목표는 "단일 실행 파일" 이다.
// 그래서 빌드 시점에 한 번 구워 넣는다.
//
//	go run ./tools/gen_width
//
// 다시 돌려도 같은 파일이 나온다(결정론). 그래야 git diff 로 표가 바뀌었는지 볼 수 있다.
package main

import (
	"bufio"
	"flag"
	"fmt"
	"os"
	"strconv"
	"strings"
)

func main() {
	in := flag.String("in", "width/widthdata.txt", "유니코드 속성 표")
	out := flag.String("out", "width/table.go", "만들어 낼 Go 파일")
	flag.Parse()

	f, err := os.Open(*in)
	if err != nil {
		die(err)
	}
	defer f.Close()

	version := ""
	type rng struct {
		lo, hi uint32
		class  byte
	}
	var rows []rng

	sc := bufio.NewScanner(f)
	for line := 1; sc.Scan(); line++ {
		t := strings.TrimSpace(sc.Text())
		if strings.HasPrefix(t, "# @version ") {
			version = strings.TrimSpace(strings.TrimPrefix(t, "# @version "))
			continue
		}
		if t == "" || strings.HasPrefix(t, "#") {
			continue
		}
		// 형식: START..END;CLASS
		semi := strings.IndexByte(t, ';')
		if semi < 0 {
			die(fmt.Errorf("%s:%d: ';' 가 없다: %q", *in, line, t))
		}
		span, class := t[:semi], t[semi+1:]
		lo, hi := span, span
		if i := strings.Index(span, ".."); i >= 0 {
			lo, hi = span[:i], span[i+2:]
		}
		a, err := strconv.ParseUint(lo, 16, 32)
		if err != nil {
			die(fmt.Errorf("%s:%d: %v", *in, line, err))
		}
		b, err := strconv.ParseUint(hi, 16, 32)
		if err != nil {
			die(fmt.Errorf("%s:%d: %v", *in, line, err))
		}
		if len(class) != 1 || strings.IndexByte("WFAZ", class[0]) < 0 {
			die(fmt.Errorf("%s:%d: 모르는 부류 %q", *in, line, class))
		}
		rows = append(rows, rng{uint32(a), uint32(b), class[0]})
	}
	if err := sc.Err(); err != nil {
		die(err)
	}
	if version == "" {
		die(fmt.Errorf("%s: '# @version' 줄이 없다 — 어느 판인지 모르는 표는 쓰지 않는다", *in))
	}

	// 이분 탐색이 성립하려면 구간이 lo 오름차순이고 겹치지 않아야 한다.
	// 원본이 그렇게 생겼더라도 여기서 한 번 확인한다 — 표가 조용히 어긋나면
	// 증상이 "가끔 한 칸 밀림" 으로만 나타나서 원인을 찾기 대단히 어렵다.
	for i := 1; i < len(rows); i++ {
		if rows[i].lo <= rows[i-1].hi {
			die(fmt.Errorf("구간이 겹치거나 순서가 틀렸다: %04X..%04X 다음에 %04X..%04X",
				rows[i-1].lo, rows[i-1].hi, rows[i].lo, rows[i].hi))
		}
	}

	var b strings.Builder
	fmt.Fprintf(&b, "// tools/gen_width 가 만든 파일이다. 손으로 고치지 말 것.\n")
	fmt.Fprintf(&b, "// 원본: %s (유니코드 %s) · 구간 %d개\n//\n", *in, version, len(rows))
	fmt.Fprintf(&b, "// 다시 만들려면: go run ./tools/gen_width\n\n")
	fmt.Fprintf(&b, "package width\n\n")
	fmt.Fprintf(&b, "// 이 표가 어느 판의 유니코드에서 왔는지. 슬라이드와 로그에 그대로 적는다.\n")
	fmt.Fprintf(&b, "const unicodeVersion = %q\n\n", version)
	fmt.Fprintf(&b, "// wrange 는 같은 폭 부류를 갖는 코드포인트 구간이다.\n")
	fmt.Fprintf(&b, "// lo 오름차순으로 정렬돼 있고 서로 겹치지 않는다 — 이분 탐색의 전제다.\n")
	fmt.Fprintf(&b, "type wrange struct {\n\tlo, hi rune\n\tclass  byte\n}\n\n")
	fmt.Fprintf(&b, "var widthRanges = [...]wrange{\n")
	for i, r := range rows {
		if i%3 == 0 {
			b.WriteString("\t")
		}
		fmt.Fprintf(&b, "{0x%04X, 0x%04X, '%c'},", r.lo, r.hi, r.class)
		if i%3 == 2 || i == len(rows)-1 {
			b.WriteString("\n")
		} else {
			b.WriteString(" ")
		}
	}
	fmt.Fprintf(&b, "}\n")

	if err := os.WriteFile(*out, []byte(b.String()), 0o644); err != nil {
		die(err)
	}
	fmt.Printf("%s → %s · 구간 %d개 · 유니코드 %s\n", *in, *out, len(rows), version)
}

func die(err error) {
	fmt.Fprintln(os.Stderr, "gen_width:", err)
	os.Exit(1)
}
