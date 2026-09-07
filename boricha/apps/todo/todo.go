// Package todo 는 첫 번째 응용 프로그램 — 할 일 목록이다.
//
// 여기까지 만든 층이 전부 쓰인다. 입력창으로 새 할 일을 받고(widgets.TextInput),
// 목록으로 고르고 거르고(widgets.List), 도움말을 키 배치에서 뽑아 그리고(widgets.Help),
// 파일 읽기·쓰기는 명령(tea.Cmd)으로 밀어낸다.
//
// 상태를 파일에 저장한다는 것이 이 앱의 핵심 교훈이다. 저장은 순수하지 않은 일이므로
// Update 안에서 하면 안 된다 — Update 는 같은 사건에 늘 같은 결과를 내야 시험할 수 있다.
// 그래서 Update 는 "저장해 달라" 는 명령을 돌려주고, 실제 쓰기는 다른 고루틴에서 일어난다.
package todo

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"time"

	"treasure/boricha/style"
	"treasure/boricha/tea"
	"treasure/boricha/widgets"
)

// Task 는 할 일 하나. JSON 으로 그대로 오간다.
type Task struct {
	Text string `json:"text"`
	Done bool   `json:"done"`
}

// Title 은 목록에 보일 글. widgets.Item 을 만족시킨다.
func (t Task) Title() string {
	box := "☐"
	if t.Done {
		box = "☑"
	}
	return box + " " + t.Text
}

// Description 은 지금은 비어 있다. 화면에 두 줄씩 쓰지 않기로 했다.
func (t Task) Description() string { return "" }

// FilterValue 는 걸러질 때 보는 글이다. 체크 상자는 빼야 한다 —
// 안 그러면 "☐" 를 쳐서 안 끝난 일만 볼 수 있게 되는데, 그건 거르기가 아니라 우연이다.
func (t Task) FilterValue() string { return t.Text }

type mode int

const (
	modeList mode = iota
	modeAdd
)

type savedMsg struct{ err error }
type loadedMsg struct {
	tasks []Task
	err   error
}

// Model 은 앱의 상태 전부다.
type Model struct {
	path  string
	tasks []Task

	list  widgets.List
	input widgets.TextInput
	help  widgets.Help

	mode   mode
	status string
	prof   style.Profile
	w, h   int
	quit   bool
}

// New 는 앱을 만든다. path 가 비면 저장하지 않는다(기록·시험용).
func New(path string) Model {
	in := widgets.NewTextInput()
	in.Prompt = "새 할 일: "
	in.Placeholder = "무엇을 해야 하나요?"
	in.CharLimit = 60
	in.Width = 40

	ls := widgets.NewList(nil, 46, 12)
	ls.Title = "할 일"

	return Model{
		path: path, list: ls, input: in, help: widgets.NewHelp(),
		status: "a 로 추가, space 로 완료 표시",
	}
}

func (m Model) Init() tea.Cmd {
	if m.path == "" {
		return nil
	}
	return loadCmd(m.path)
}

// loadCmd 와 saveCmd 가 이 앱에서 유일하게 순수하지 않은 부분이다.
// 둘 다 명령으로 감싸 두었으므로 Update 는 순수한 채로 남는다.
func loadCmd(path string) tea.Cmd {
	return func() tea.Msg {
		b, err := os.ReadFile(path)
		if err != nil {
			if os.IsNotExist(err) {
				return loadedMsg{} // 파일이 없는 것은 오류가 아니다 — 첫 실행이다
			}
			return loadedMsg{err: err}
		}
		var ts []Task
		if err := json.Unmarshal(b, &ts); err != nil {
			return loadedMsg{err: err}
		}
		return loadedMsg{tasks: ts}
	}
}

func saveCmd(path string, tasks []Task) tea.Cmd {
	// 넘겨받은 슬라이스를 그대로 들고 가면 안 된다. 이 명령이 도는 동안
	// 주 고루틴이 tasks 를 고칠 수 있고, 그러면 무엇이 저장될지 아무도 모른다.
	snapshot := append([]Task(nil), tasks...)
	return func() tea.Msg {
		b, err := json.MarshalIndent(snapshot, "", " ")
		if err != nil {
			return savedMsg{err: err}
		}
		if dir := filepath.Dir(path); dir != "." {
			_ = os.MkdirAll(dir, 0o755)
		}
		// 임시 파일에 쓰고 이름을 바꾼다. 쓰는 도중에 전원이 나가도
		// 원래 파일이 반쯤 지워진 채로 남지 않는다.
		tmp := path + ".tmp"
		if err := os.WriteFile(tmp, append(b, '\n'), 0o644); err != nil {
			return savedMsg{err: err}
		}
		return savedMsg{err: os.Rename(tmp, path)}
	}
}

func (m Model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		m.w, m.h = msg.Width, msg.Height
		return m.resize(), nil

	case tea.ColorProfileMsg:
		m.prof = msg.Profile
		m.help = m.help.Profile(msg.Profile)
		m.list.SelectedStyle = style.New().Profile(msg.Profile).Bold(true).Foreground("205")
		m.list.TitleStyle = style.New().Profile(msg.Profile).Bold(true)
		return m, nil

	case loadedMsg:
		if msg.err != nil {
			m.status = "불러오기 실패: " + msg.err.Error()
			return m, nil
		}
		m.tasks = msg.tasks
		m.status = fmt.Sprintf("%d개를 불러왔다", len(m.tasks))
		return m.sync(), nil

	case savedMsg:
		if msg.err != nil {
			m.status = "저장 실패: " + msg.err.Error()
		} else {
			m.status = "저장함 " + time.Now().Format("15:04:05")
		}
		return m, nil

	case tea.KeyMsg:
		if m.mode == modeAdd {
			return m.updateAdd(msg)
		}
		return m.updateList(msg)
	}

	// 그 밖의 사건은 지금 초점이 있는 부품에게.
	var cmd tea.Cmd
	if m.mode == modeAdd {
		m.input, cmd = m.input.Update(msg)
	} else {
		m.list, cmd = m.list.Update(msg)
	}
	return m, cmd
}

func (m Model) updateAdd(k tea.KeyMsg) (tea.Model, tea.Cmd) {
	switch k.String() {
	case "esc":
		m.mode = modeList
		m.input = m.input.Reset().Blur()
		m.status = "취소함"
		return m, nil
	case "enter":
		text := strings.TrimSpace(m.input.Value())
		m.mode = modeList
		m.input = m.input.Reset().Blur()
		if text == "" {
			m.status = "빈 할 일은 넣지 않는다"
			return m, nil
		}
		m.tasks = append(append([]Task{}, m.tasks...), Task{Text: text})
		m.status = "추가함: " + text
		m = m.sync()
		return m, m.save()
	}
	var cmd tea.Cmd
	m.input, cmd = m.input.Update(k)
	return m, cmd
}

func (m Model) updateList(k tea.KeyMsg) (tea.Model, tea.Cmd) {
	// 거르는 중이면 키는 전부 목록이 가져간다 — 안 그러면 "차" 를 칠 수 없다.
	if m.list.Filtering() {
		var cmd tea.Cmd
		m.list, cmd = m.list.Update(k)
		return m, cmd
	}
	switch k.String() {
	case "q", "ctrl+c":
		m.quit = true
		return m, tea.Quit
	case "a", "n":
		m.mode = modeAdd
		m.input = m.input.Focus()
		m.status = "적고 enter, esc 로 취소"
		return m, nil
	case " ", "space", "enter":
		if i := m.taskIndex(); i >= 0 {
			ts := append([]Task{}, m.tasks...)
			ts[i].Done = !ts[i].Done
			m.tasks = ts
			m = m.sync()
			return m, m.save()
		}
		return m, nil
	case "d", "delete":
		if i := m.taskIndex(); i >= 0 {
			ts := append([]Task{}, m.tasks[:i]...)
			m.tasks = append(ts, m.tasks[i+1:]...)
			m.status = "지움"
			m = m.sync()
			return m, m.save()
		}
		return m, nil
	case "?":
		m.help.ShowAll = !m.help.ShowAll
		return m.resize(), nil
	}
	var cmd tea.Cmd
	m.list, cmd = m.list.Update(k)
	return m, cmd
}

// taskItem 은 목록에 넣을 때 원래 자리 번호를 함께 들고 다니는 포장이다.
//
// 왜 필요한가. 목록이 걸러져 있으면 목록의 번호와 tasks 의 번호가 다르다.
// 그렇다고 고른 항목의 **값** 으로 tasks 를 뒤지면, 글이 똑같은 할 일이 둘일 때
// 언제나 앞의 것을 찾는다 — 두 번째 "우유 사기" 를 지웠는데 첫 번째가 사라진다.
// 자리 번호를 항목에 붙여 두면 그 문제가 아예 없어진다.
type taskItem struct {
	Task
	idx int
}

func (m Model) taskIndex() int {
	sel, ok := m.list.SelectedItem().(taskItem)
	if !ok {
		return -1
	}
	return sel.idx
}

// sync 는 tasks 를 목록 부품에 다시 넣는다. 상태의 출처는 언제나 tasks 하나다.
func (m Model) sync() Model {
	its := make([]widgets.Item, len(m.tasks))
	for i, t := range m.tasks {
		its[i] = taskItem{Task: t, idx: i}
	}
	m.list = m.list.SetItems(its)
	return m
}

func (m Model) save() tea.Cmd {
	if m.path == "" {
		return nil
	}
	return saveCmd(m.path, m.tasks)
}

func (m Model) resize() Model {
	w := m.w - 4
	if w < 20 {
		w = 20
	}
	h := m.h - 6
	if m.help.ShowAll {
		h -= 5
	}
	if h < 4 {
		h = 4
	}
	m.list.Width, m.list.Height = w, h
	m.input.Width = w - 10
	return m
}

func (m Model) bindings() []widgets.Binding {
	hasTask := len(m.tasks) > 0
	return []widgets.Binding{
		widgets.NewBinding("a", "추가", "a", "n"),
		widgets.NewBinding("space", "완료 표시", " ").SetEnabled(hasTask),
		widgets.NewBinding("d", "지우기", "d").SetEnabled(hasTask),
		widgets.NewBinding("/", "거르기", "/").SetEnabled(hasTask),
		widgets.NewBinding("↑/↓", "옮기기", "up", "down").SetEnabled(hasTask),
		widgets.NewBinding("?", "도움말", "?"),
		widgets.NewBinding("q", "끝내기", "q"),
	}
}

func (m Model) View() string {
	base := style.New().Profile(m.prof)
	done := 0
	for _, t := range m.tasks {
		if t.Done {
			done++
		}
	}
	head := base.Bold(true).Render("🍵 할 일") + "  " +
		base.Faint(true).Render(fmt.Sprintf("%d/%d 끝냄", done, len(m.tasks)))

	body := m.list.View()
	if m.mode == modeAdd {
		body = m.input.View() + "\n" + body
	}

	return style.JoinVertical(style.Left,
		head,
		base.Border(style.RoundedBorder).Padding(0, 1).Render(body),
		base.Faint(true).Render(m.status),
		m.help.View(m.bindings()),
	)
}
