// record — 모델을 터미널 없이 돌려 화면을 한 장씩 기록한다.
//
//	go run ./tools/record -name width_bad -out out/frames_width_bad.json
//	go run ./tools/record -list
//
// 왜 필요한가. 덱에 "이렇게 보입니다" 하고 손으로 그린 화면을 실으면 그건 거짓말이 된다.
// 코드가 바뀌어도 그림은 안 바뀌기 때문이다. 그래서 화면은 전부 여기서 뽑는다 —
// 각본을 정해 두고, 진짜 모델을 돌려서, 진짜 View 문자열을 저장한다.
//
// 결정론이 이 도구의 전부다. 같은 각본을 두 번 돌리면 파일이 바이트까지 같아야
// `make record` 뒤의 git diff 가 비어 있고, 덱의 그림이 소스와 어긋나지 않는다.
// 그 성질은 testkit 이 보장한다 — 시계도 고루틴도 쓰지 않는다.
package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"sort"

	"time"

	"treasure/boricha/apps/bugs"
	"treasure/boricha/apps/monitor"
	"treasure/boricha/apps/showcase"
	"treasure/boricha/apps/todo"
	"treasure/boricha/style"
	"treasure/boricha/tea"
	"treasure/boricha/testkit"
	"treasure/boricha/widgets"
)

// Frame 하나 = 어떤 조작 직후의 화면 전체.
// 필드 이름은 tools/ansi2html 이 읽는 것과 맞춰 둔다.
type Frame struct {
	I       int    `json:"i"`
	Label   string `json:"label"`
	Content string `json:"content"`
}

// Recording 은 한 번의 기록 전체.
type Recording struct {
	Name   string  `json:"name"`
	Script string  `json:"script"`
	Frames []Frame `json:"frames"`
}

// entry 는 기록 등록부의 한 줄이다.
//
// 왜 등록부를 두는가. 기록할 대상이 라이브러리 패키지의 모델이어야 하기 때문이다
// (예제들은 package main 이라 여기서 import 할 수 없다 — 그건 예제가 "그 파일 하나로
// 완결된 프로그램" 이어야 한다는 요구와 맞바꾼 것이고, 예제의 증거는 tmux 캡처가 맡는다).
type entry struct {
	model  func() tea.Model
	script string
	desc   string
}

var registry = map[string]entry{
	"width_bad": {
		model:  func() tea.Model { return bugs.NewWidth(false) },
		script: `56x12 <down> <down> .1`,
		desc:   "함정 1 — len 으로 칸을 세면 한글 줄만 밀린다",
	},
	"width_ok": {
		model:  func() tea.Model { return bugs.NewWidth(true) },
		script: `56x12 <down> <down> .1`,
		desc:   "함정 1 고친 판 — width.Pad 는 칸을 센다",
	},
	"tick_bad": {
		model:  func() tea.Model { return bugs.NewTick(false) },
		script: `48x10 .8`,
		desc:   "함정 2 — Tick 을 다시 걸지 않으면 한 번 울리고 멎는다",
	},
	"todo": {
		model: func() tea.Model { return todo.New("") },
		script: `70x20 a "보리차 사기" <enter> a "찻잔 씻기" <enter> a "덱 마무리" <enter> ` +
			`<down> <space> <up> / "차" <enter> <esc> ?`,
		desc: "할 일 목록 — 추가·완료·거르기·도움말",
	},
	"monitor": {
		// 간격을 줄인다. testkit 의 기다리기는 진짜 잠이라, 기본 0.7초로 두면
		// 프레임 열 장을 뽑는 데 7초가 걸린다.
		model:  func() tea.Model { return monitor.New().SetInterval(30 * time.Millisecond) },
		script: `76x22 .8 <space> .2 <space> .4`,
		desc:   "시스템 모니터 — 표본 수집·멈춤·다시",
	},
	"showcase": {
		model: func() tea.Model {
			return showcase.New().SetSpinner(widgets.SpinnerSet{
				Frames: []string{"🫖", "🍵"}, FPS: 5 * time.Millisecond})
		},
		script: `76x22 <tab> <tab> <tab> "보리차" <tab>`,
		desc:   "전시장 — 꾸미기·색·글자 폭·입력 탭",
	},
	"tick_ok": {
		model:  func() tea.Model { return bugs.NewTick(true) },
		script: `48x10 .8`,
		desc:   "함정 2 고친 판 — 울림을 받은 자리에서 다시 건다",
	},
}

func main() {
	name := flag.String("name", "", "등록부의 이름")
	out := flag.String("out", "", "쓸 파일")
	list := flag.Bool("list", false, "등록부를 보여 준다")
	flag.Parse()

	if *list {
		names := make([]string, 0, len(registry))
		for k := range registry {
			names = append(names, k)
		}
		sort.Strings(names)
		for _, n := range names {
			fmt.Printf("%-12s %s\n      %s\n", n, registry[n].desc, registry[n].script)
		}
		return
	}

	e, ok := registry[*name]
	if !ok {
		fmt.Fprintf(os.Stderr, "record: 등록부에 %q 가 없다 (-list 로 확인)\n", *name)
		os.Exit(2)
	}

	// 색 수준을 못박는다. 환경 변수를 보고 정하게 두면 같은 명령이 기계마다 다른
	// 파일을 만들어 낸다 — 결정론이 깨지는 가장 흔한 자리다.
	r, err := testkit.Run(e.model(), e.script, testkit.Options{Profile: style.ANSI256})
	if err != nil {
		fmt.Fprintln(os.Stderr, "record:", err)
		os.Exit(1)
	}

	rec := Recording{Name: *name, Script: e.script}
	for i, f := range r.Frames {
		rec.Frames = append(rec.Frames, Frame{I: i, Label: r.Labels[i], Content: f})
	}

	b, err := json.MarshalIndent(rec, "", " ")
	if err != nil {
		fmt.Fprintln(os.Stderr, "record:", err)
		os.Exit(1)
	}
	b = append(b, '\n')
	if *out == "" {
		os.Stdout.Write(b)
		return
	}
	if err := os.WriteFile(*out, b, 0o644); err != nil {
		fmt.Fprintln(os.Stderr, "record:", err)
		os.Exit(1)
	}
	fmt.Printf("%s · %d프레임 · %d×%d → %s\n", *name, len(rec.Frames), r.Cols, r.Rows, *out)
}
