// minipuppy — Code Puppy 의 뼈대를 Go 로 다시 만든 코딩 에이전트.
//
//	minipuppy                      대화형 REPL
//	minipuppy -p "이 함수 고쳐"     한 번 돌고 끝(파이프·CI 용)
package main

import (
	"bufio"
	"context"
	"flag"
	"fmt"
	"os"
	"os/signal"
	"path/filepath"
	"sort"
	"strings"
	"time"

	mp "minipuppy"
)

const banner = `
   ___  ___       _        ___
  |     |  |  ___  |         |
  |__   |__|  |    |  ___    |    minipuppy — Go 로 다시 만든 Code Puppy
  |     |  |  |    |  |  |   |    /help 로 명령 목록, /quit 로 끝
  |     |  |  |__  |  |__|   |
`

type shell struct {
	cfg     *mp.Config
	bus     *mp.Bus
	tools   *mp.Registry
	agents  *mp.AgentRegistry
	models  map[string]mp.ModelSpec
	ws      *mp.Workspace
	store   mp.Store
	sess    *mp.Session
	hist    *mp.History
	stdin   *bufio.Reader
	model   string
	agent   string
	running bool
}

func newShell(root, configDir string) (*shell, error) {
	cfg := mp.NewConfig(configDir, nil)
	bus := mp.NewBus(mp.ConsoleSink)
	tools := mp.NewRegistry()
	mp.RegisterFileTools(tools)
	mp.RegisterShellTools(tools, time.Duration(cfg.Int("command_timeout"))*time.Second)
	agents := mp.NewAgentRegistry(cfg.AgentsDir())
	ws, err := mp.NewWorkspace(root)
	if err != nil {
		return nil, err
	}
	ws.Yolo = cfg.Bool("yolo_mode")
	models := mp.LoadModels(filepath.Join(cfg.Dir, "models.json"))
	sh := &shell{cfg: cfg, bus: bus, tools: tools, agents: agents,
		models: models, ws: ws, store: mp.Store{Dir: cfg.SessionsDir()},
		stdin: bufio.NewReader(os.Stdin),
		model: cfg.Get("model"), agent: cfg.Get("agent"), running: true}
	sh.sess = mp.NewSession(sh.agent)
	ws.Approver = sh.ask
	mp.RegisterSubagentTool(tools, agents, sh.modelFor, bus,
		mp.LimitsFrom(cfg), cfg.Int("max_subagent_depth"))
	return sh, nil
}

// ask 는 되돌릴 수 없는 일 앞에서 사람에게 묻는 창구.
func (s *shell) ask(action, rel string) bool {
	fmt.Printf("  %s %s — 할까? [y/N] ", action, rel)
	line, err := s.stdin.ReadString(byte('\n'))
	if err != nil {
		return false
	}
	a := strings.ToLower(strings.TrimSpace(line))
	return a == "y" || a == "yes" || a == "예"
}

func (s *shell) modelFor(spec mp.AgentSpec) (mp.Model, error) {
	name := spec.ModelName
	if name == "" {
		name = s.model
	}
	return mp.BuildModel(name, s.models, s.cfg.Env)
}

func (s *shell) turn(ctx context.Context, text string) {
	switch {
	case strings.HasPrefix(text, "/"):
		s.slash(strings.TrimPrefix(text, "/"))
		return
	case strings.HasPrefix(text, "!"):
		s.slash("sh " + strings.TrimPrefix(text, "!"))
		return
	}
	model, err := mp.BuildModel(s.model, s.models, s.cfg.Env)
	if err != nil {
		s.bus.Errorf("%v", err)
		return
	}
	agent, err := s.agents.Build(s.agent, model, s.tools, s.bus, mp.LimitsFrom(s.cfg))
	if err != nil {
		s.bus.Errorf("%v", err)
		return
	}
	if s.hist == nil {
		s.hist = agent.NewHistory()
	}
	res, h := agent.Run(ctx, text, s.hist, s.ws)
	s.hist = h
	if res.Stopped != mp.StopDone {
		s.bus.Warnf("멈춘 이유: %s %s", res.Stopped, res.Err)
	}
	s.sess.Messages = h.Msgs
	s.sess.Agent = s.agent
	if s.sess.Title == "" {
		s.sess.Title = firstRunes(text, 40)
	}
	if err := s.store.Save(s.sess); err != nil {
		s.bus.Warnf("세션 저장 실패: %v", err)
	}
}

var helpText = strings.Join([]string{
	"/help         명령 목록",
	"/agent [이름] 에이전트 보기·바꾸기",
	"/model [이름] 모델 보기·바꾸기",
	"/tools        지금 쓸 수 있는 도구",
	"/compact      지금 바로 기록을 접는다",
	"/config       설정 보기 / key=value 로 쓰기",
	"/session      세션 목록 / load <id> / new",
	"/sh <명령>    셸 명령 실행",
	"/quit         끝낸다",
}, "\n")

func (s *shell) slash(line string) {
	name, rest, _ := strings.Cut(line, " ")
	rest = strings.TrimSpace(rest)
	switch name {
	case "help":
		s.bus.Infof("%s", helpText)
	case "agent":
		s.cmdAgent(rest)
	case "model":
		s.cmdModel(rest)
	case "tools":
		s.cmdTools()
	case "compact":
		s.cmdCompact()
	case "config":
		s.cmdConfig(rest)
	case "session":
		s.cmdSession(rest)
	case "sh":
		s.cmdShell(rest)
	case "quit", "exit":
		s.running = false
	default:
		s.bus.Warnf("모르는 명령: /%s — /help 를 봐라", name)
	}
}

func (s *shell) cmdAgent(rest string) {
	if rest == "" {
		s.bus.Infof("지금: %s\n%s", s.agent, s.agents.Describe())
		return
	}
	if _, ok := s.agents.Get(rest); !ok {
		s.bus.Warnf("모르는 에이전트: %s", rest)
		return
	}
	// 인격이 바뀌면 시스템 프롬프트가 바뀐다 -> 기록을 새로 시작한다.
	s.agent, s.hist = rest, nil
	s.bus.Infof("에이전트를 %s 로 바꿨다. 대화 기록은 새로 시작한다.", rest)
}

func (s *shell) cmdModel(rest string) {
	if rest == "" {
		s.bus.Infof("지금: %s\n있는 것: %s", s.model, strings.Join(sortedKeys(s.models), ", "))
		return
	}
	if _, ok := s.models[rest]; !ok {
		s.bus.Warnf("models.json 에 없다: %s", rest)
		return
	}
	// 모델은 인격이 아니다. 기록은 그대로 두고 갈아 끼운다.
	s.model = rest
	s.bus.Infof("모델을 %s 로 바꿨다. 대화 기록은 그대로다.", rest)
}

func (s *shell) cmdTools() {
	spec, _ := s.agents.Get(s.agent)
	var b strings.Builder
	for _, t := range s.tools.Allowed(spec.Tools) {
		fmt.Fprintf(&b, "%-16s %s\n", t.Name, t.Description)
	}
	allow := map[string]bool{}
	for _, a := range spec.Tools {
		allow[a] = true
	}
	var blocked []string
	for _, n := range s.tools.Names() {
		if spec.Tools != nil && !allow[n] {
			blocked = append(blocked, n)
		}
	}
	out := strings.TrimRight(b.String(), "\n")
	if len(blocked) > 0 {
		out += "\n\n막힌 도구: " + strings.Join(blocked, ", ")
	}
	s.bus.Infof("%s", out)
}

func (s *shell) cmdCompact() {
	if s.hist == nil {
		s.bus.Infof("접을 기록이 없다.")
		return
	}
	before := s.hist.TotalTokens()
	n, _ := s.hist.Compact(s.cfg.Int("protected_tokens"))
	if n == 0 {
		s.bus.Infof("접을 중간 구간이 없다. (%d토큰)", before)
		return
	}
	s.bus.Infof("%d건을 접었다. %d -> %d토큰", n, before, s.hist.TotalTokens())
}

func (s *shell) cmdConfig(rest string) {
	if k, v, ok := strings.Cut(rest, "="); ok {
		k, v = strings.TrimSpace(k), strings.TrimSpace(v)
		if err := s.cfg.Set(k, v); err != nil {
			s.bus.Errorf("%v", err)
			return
		}
		s.bus.Infof("%s = %s (%s 층)", k, s.cfg.Get(k), s.cfg.Source(k))
		return
	}
	all := s.cfg.All()
	keys := make([]string, 0, len(all))
	for k := range all {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	var b strings.Builder
	for _, k := range keys {
		fmt.Fprintf(&b, "%-22s %-8s %s\n", k, s.cfg.Source(k), all[k])
	}
	s.bus.Infof("%s", strings.TrimRight(b.String(), "\n"))
}

func (s *shell) cmdSession(rest string) {
	verb, id, _ := strings.Cut(rest, " ")
	switch verb {
	case "new":
		s.sess, s.hist = mp.NewSession(s.agent), nil
		s.bus.Infof("새 세션: %s", s.sess.ID)
	case "load":
		got, err := s.store.Load(strings.TrimSpace(id))
		if err != nil {
			s.bus.Warnf("못 열었다: %v", err)
			return
		}
		s.sess = got
		s.hist = &mp.History{Msgs: got.Messages}
		if got.Agent != "" {
			s.agent = got.Agent
		}
		s.bus.Infof("세션 %s 를 이어 연다 (메시지 %d건)", got.ID, len(got.Messages))
	default:
		var b strings.Builder
		for _, x := range s.store.List() {
			title := x.Title
			if title == "" {
				title = "(제목 없음)"
			}
			fmt.Fprintf(&b, "%s  %-20s %d건\n", x.ID, firstRunes(title, 20), len(x.Messages))
		}
		if b.Len() == 0 {
			s.bus.Infof("(저장된 세션 없음)")
			return
		}
		s.bus.Infof("%s", strings.TrimRight(b.String(), "\n"))
	}
}

func (s *shell) cmdShell(rest string) {
	if rest == "" {
		s.bus.Warnf("실행할 명령을 줘라.")
		return
	}
	out := s.tools.Call(s.ws, "run_command", map[string]any{"command": rest},
		nil, s.cfg.Int("max_tool_output"))
	kind := mp.KindToolOut
	if !out.OK {
		kind = mp.KindError
	}
	s.bus.Emit(kind, out.Content)
}

func sortedKeys(m map[string]mp.ModelSpec) []string {
	out := make([]string, 0, len(m))
	for k := range m {
		out = append(out, k)
	}
	sort.Strings(out)
	return out
}

func firstRunes(s string, n int) string {
	r := []rune(s)
	if len(r) <= n {
		return s
	}
	return string(r[:n])
}

func main() {
	prompt := flag.String("p", "", "한 번만 돌리고 끝낸다")
	root := flag.String("C", ".", "작업 뿌리")
	configDir := flag.String("config-dir", "", "설정 디렉터리")
	agentName := flag.String("agent", "", "시작 에이전트")
	modelName := flag.String("model", "", "시작 모델")
	yolo := flag.Bool("yolo", false, "쓰기 확인을 묻지 않는다")
	quiet := flag.Bool("quiet", false, "배너를 안 그린다")
	flag.Parse()

	sh, err := newShell(*root, *configDir)
	if err != nil {
		fmt.Fprintln(os.Stderr, "시작 실패:", err)
		os.Exit(2)
	}
	if *agentName != "" {
		sh.agent = *agentName
	}
	if *modelName != "" {
		sh.model = *modelName
	}
	if *yolo {
		sh.ws.Yolo = true
	}

	// Ctrl-C 는 프로그램을 죽이지 않는다. context 를 닫아 루프가 걸음 사이에서
	// 스스로 멈추게 한다 — 도구 실행 한복판에서 끊으면 파일이 반쯤 쓰인다.
	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt)
	defer stop()

	if *prompt != "" { // 한 번 모드 — 물어볼 사람이 없으니 확인을 건너뛴다
		sh.ws.Yolo = true
		sh.turn(ctx, *prompt)
		return
	}
	if !*quiet {
		fmt.Print(banner)
		fmt.Println("  뿌리:", sh.ws.Root)
		fmt.Printf("  에이전트: %s   모델: %s\n\n", sh.agent, sh.model)
	}
	for sh.running {
		fmt.Print("🐶 > ")
		line, err := sh.stdin.ReadString(byte('\n'))
		if err != nil && strings.TrimSpace(line) == "" {
			fmt.Println()
			break
		}
		line = strings.TrimSpace(line)
		if line == "" {
			continue
		}
		sh.turn(ctx, line)
	}
}
