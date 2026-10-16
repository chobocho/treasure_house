// Package barestore 는 맨손 Task 저장소다 — 맵 하나와 상태 전이 표.
//
// bare_lodging(맨손 숙소 에이전트)이 쓰고, store_rules 가 전이 규칙을
// 시험한다. 표준 라이브러리(sync·time·uuid)만 쓴다.
package barestore

import (
	"fmt"
	"slices"
	"sync"
	"time"
	"uuid"
)

// region: types
// Part 는 받은 JSON 객체 그대로 — text·raw·url·data 중 하나가 키다.
type Part map[string]any

// 필드 차례가 곧 와이어의 키 차례다(proto 의 차례에 맞췄다).
type Message struct {
	MessageID        string         `json:"messageId"`
	ContextID        string         `json:"contextId,omitempty"`
	TaskID           string         `json:"taskId,omitempty"`
	Role             string         `json:"role"`
	Parts            []Part         `json:"parts"`
	Metadata         map[string]any `json:"metadata,omitempty"`
	Extensions       []string       `json:"extensions,omitempty"`
	ReferenceTaskIDs []string       `json:"referenceTaskIds,omitempty"`
}

type Status struct {
	State     string   `json:"state"`
	Message   *Message `json:"message,omitempty"`
	Timestamp string   `json:"timestamp"`
}

type Artifact struct {
	ArtifactID string `json:"artifactId"`
	Name       string `json:"name"`
	Parts      []Part `json:"parts"`
}

type Task struct {
	ID        string     `json:"id"`
	ContextID string     `json:"contextId"`
	Status    Status     `json:"status"`
	Artifacts []Artifact `json:"artifacts,omitempty"`
	History   []Message  `json:"history,omitempty"`
}

// endregion

// region: events
// Event 는 StreamResponse — 셋 중 하나만 채운다.
type Event struct {
	Task           *Task           `json:"task,omitempty"`
	StatusUpdate   *StatusUpdate   `json:"statusUpdate,omitempty"`
	ArtifactUpdate *ArtifactUpdate `json:"artifactUpdate,omitempty"`
}

type StatusUpdate struct {
	TaskID    string `json:"taskId"`
	ContextID string `json:"contextId"`
	Status    Status `json:"status"`
}

type ArtifactUpdate struct {
	TaskID    string   `json:"taskId"`
	ContextID string   `json:"contextId"`
	Artifact  Artifact `json:"artifact"`
}

// endregion

// region: states
const (
	Submitted     = "TASK_STATE_SUBMITTED"
	Working       = "TASK_STATE_WORKING"
	InputRequired = "TASK_STATE_INPUT_REQUIRED"
	AuthRequired  = "TASK_STATE_AUTH_REQUIRED"
	Completed     = "TASK_STATE_COMPLETED"
	Failed        = "TASK_STATE_FAILED"
	Canceled      = "TASK_STATE_CANCELED"
	Rejected      = "TASK_STATE_REJECTED"
)

// 지금 상태 → 옮겨 갈 수 있는 상태. 스펙에는 이런 표가 없다(5부).
// 뒤로(Submitted) 가지 않고, 종료 넷에서는 나갈 곳이 없다.
var allowed = map[string][]string{
	Submitted: {Working, InputRequired, AuthRequired,
		Completed, Failed, Canceled, Rejected},
	Working: {Working, InputRequired, AuthRequired,
		Completed, Failed, Canceled, Rejected},
	InputRequired: {Working, Canceled},
	AuthRequired:  {Working, Canceled},
}

// IllegalMove 는 표에 없는 전이 — 실행기의 버그다.
type IllegalMove struct{ From, To string }

func (e IllegalMove) Error() string {
	return fmt.Sprintf("%s → %s", e.From, e.To)
}

// CanMove: 종료 상태는 표에 없으니 nil 목록 — 늘 false.
func CanMove(src, dst string) bool {
	return slices.Contains(allowed[src], dst)
}

// endregion

// region: ids
// NewID 는 작업·맥락·메시지·아티팩트 id — UUID 판 4(무작위).
// uuid 는 이 기계의 Go 1.27 표준 라이브러리에 있는 패키지다.
func NewID() string { return uuid.New().String() }

// Now 는 §5.6.1 의 꼴 — UTC, 밀리초, 끝은 Z.
func Now() string {
	return time.Now().UTC().Format("2006-01-02T15:04:05.000Z")
}

// endregion

// region: store
// Store 는 taskID → Task. net/http 는 요청마다 고루틴을 띄우므로
// 저장소를 만지는 동안은 Mu 를 잡는다(잡는 쪽은 부르는 쪽).
type Store struct {
	Mu    sync.Mutex
	tasks map[string]*Task
}

func New() *Store { return &Store{tasks: map[string]*Task{}} }

// Create 는 첫 메시지로 새 Task 를 짓는다 — 상태는 Submitted.
func (s *Store) Create(msg Message) *Task {
	ctx := msg.ContextID // 클라이언트가 정해 왔으면 그대로(§3.4.1)
	if ctx == "" {
		ctx = NewID()
	}
	t := &Task{ID: NewID(), ContextID: ctx,
		Status: Status{State: Submitted, Timestamp: Now()}}
	s.tasks[t.ID] = t
	s.Append(t, msg)
	return t
}

func (s *Store) Get(id string) *Task { return s.tasks[id] }

// Append 는 받은 메시지를 이력에 넣는다 — 두 id 를 채워서.
func (s *Store) Append(t *Task, msg Message) {
	msg.ContextID, msg.TaskID = t.ContextID, t.ID // 값 복사본이다
	t.History = append(t.History, msg)
}

// endregion

// region: move
// Move 는 상태를 옮기고, 그 일을 알리는 스트림 이벤트를 돌려준다.
// 지난 상태의 메시지(에이전트의 물음)는 이력으로 내린다.
func Move(t *Task, state string, parts ...Part) (Event, error) {
	if !CanMove(t.Status.State, state) {
		return Event{}, IllegalMove{t.Status.State, state}
	}
	if t.Status.Message != nil {
		t.History = append(t.History, *t.Status.Message)
	}
	st := Status{State: state}
	if len(parts) > 0 {
		st.Message = &Message{MessageID: NewID(),
			ContextID: t.ContextID, TaskID: t.ID,
			Role: "ROLE_AGENT", Parts: parts}
	}
	st.Timestamp = Now()
	t.Status = st // 구조체 값이라 이벤트에는 복사본이 간다
	return Event{StatusUpdate: &StatusUpdate{
		TaskID: t.ID, ContextID: t.ContextID, Status: st}}, nil
}

// endregion

// region: artifact
// AddArtifact 는 아티팩트를 붙이고, 그 일을 알리는 이벤트를 돌려준다.
func AddArtifact(t *Task, name string, parts ...Part) Event {
	a := Artifact{ArtifactID: NewID(), Name: name, Parts: parts}
	t.Artifacts = append(t.Artifacts, a)
	return Event{ArtifactUpdate: &ArtifactUpdate{
		TaskID: t.ID, ContextID: t.ContextID, Artifact: a}}
}

// endregion

// region: view
// View 는 와이어로 내보낼 Task — 이력은 최근 n 개만(n < 0 이면 전부).
// 슬라이스를 새로 복사해 담는다: 잠금을 놓은 뒤 다른 요청이 작업을
// 고쳐도, 이미 떠 둔 모습은 그대로다.
func View(t *Task, n int) *Task {
	v := *t
	v.Artifacts = slices.Clone(t.Artifacts)
	h := t.History
	if n >= 0 && n < len(h) { // 0 이면 이력 없이(§3.2.4)
		h = h[len(h)-n:]
	}
	v.History = slices.Clone(h)
	return &v
}

// endregion
