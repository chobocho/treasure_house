// Package filestore 는 Task 를 파일 하나씩(JSON)으로 두는
// taskstore.Store 다. 교재용이라 작게: 소유자 구분·페이지 토큰은
// 뺐고, 목록은 파일을 다 읽는다.
package filestore

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io/fs"
	"os"
	"path/filepath"
	"regexp"
	"slices"
	"strings"
	"sync"
	"time"

	"github.com/a2aproject/a2a-go/v2/a2a"
	"github.com/a2aproject/a2a-go/v2/a2asrv/taskstore"
)

// record 는 파일 하나의 내용 — Task 와 그 판 번호
type record struct {
	Version taskstore.TaskVersion `json:"version"`
	Task    *a2a.Task             `json:"task"`
}

// Store 의 mu 는 "판 번호 비교 → 쓰기" 를 한 덩어리로 묶는다.
type Store struct {
	dir string
	mu  sync.Mutex
}

var _ taskstore.Store = (*Store)(nil)

func New(dir string) (*Store, error) {
	return &Store{dir: dir}, os.MkdirAll(dir, 0o755)
}

// region: path
var safeID = regexp.MustCompile(`^[A-Za-z0-9_-]{1,64}$`)

// taskId 는 클라이언트가 보낸 글자다 — 파일 이름이 되기 전에 거른다
func (s *Store) path(id a2a.TaskID) (string, error) {
	if !safeID.MatchString(string(id)) {
		return "", a2a.ErrTaskNotFound
	}
	return filepath.Join(s.dir, string(id)+".json"), nil
}

// endregion

func (s *Store) read(id a2a.TaskID) (*record, error) {
	p, err := s.path(id)
	if err != nil {
		return nil, err
	}
	b, err := os.ReadFile(p)
	if errors.Is(err, fs.ErrNotExist) {
		return nil, a2a.ErrTaskNotFound // → -32001
	}
	if err != nil {
		return nil, err
	}
	var r record
	return &r, json.Unmarshal(b, &r)
}

// region: write
func (s *Store) write(r *record) error {
	p, err := s.path(r.Task.ID)
	if err != nil {
		return err
	}
	b, err := json.Marshal(r)
	if err != nil {
		return err
	}
	if err := os.WriteFile(p+".tmp", b, 0o644); err != nil {
		return err
	}
	return os.Rename(p+".tmp", p) // 바꿔 끼우기는 원자적
}

// endregion

func (s *Store) Create(
	ctx context.Context, t *a2a.Task,
) (taskstore.TaskVersion, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if _, err := s.read(t.ID); err == nil {
		return 0, taskstore.ErrTaskAlreadyExists
	}
	return 1, s.write(&record{Version: 1, Task: t})
}

// region: update
func (s *Store) Update(
	ctx context.Context, u *taskstore.UpdateRequest,
) (taskstore.TaskVersion, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	r, err := s.read(u.Task.ID)
	if err != nil {
		return 0, err
	}
	// 앞 판이 맞아야 고쳐 쓴다(SDK 가 MUST 로 요구하는 계약)
	if u.PrevVersion != taskstore.TaskVersionMissing &&
		u.PrevVersion != r.Version {
		return 0, taskstore.ErrConcurrentModification
	}
	r.Version, r.Task = r.Version+1, u.Task
	return r.Version, s.write(r)
}

// endregion

func (s *Store) Get(
	ctx context.Context, id a2a.TaskID,
) (*taskstore.StoredTask, error) {
	r, err := s.read(id)
	if err != nil {
		return nil, err
	}
	return &taskstore.StoredTask{Task: r.Task, Version: r.Version}, nil
}

// region: list
func (s *Store) List(
	ctx context.Context, q *a2a.ListTasksRequest,
) (*a2a.ListTasksResponse, error) {
	var tasks []*a2a.Task
	for _, r := range s.all() {
		t := r.Task
		if q.ContextID != "" && t.ContextID != q.ContextID ||
			q.Status != a2a.TaskStateUnspecified &&
				t.Status.State != q.Status {
			continue
		}
		if !q.IncludeArtifacts { // Go 에서는 저장소의 몫이다
			t.Artifacts = nil
		}
		tasks = append(tasks, t)
	}
	// 새것부터(상태 시각), 같으면 id — InMemory 와 같은 차례
	slices.SortFunc(tasks, func(a, b *a2a.Task) int {
		if c := stamp(b).Compare(stamp(a)); c != 0 {
			return c
		}
		return strings.Compare(string(b.ID), string(a.ID))
	})
	size := q.PageSize
	if size == 0 {
		size = 50
	}
	res := &a2a.ListTasksResponse{TotalSize: len(tasks), PageSize: size}
	res.Tasks = tasks[:min(size, len(tasks))]
	return res, nil
}

// endregion

func stamp(t *a2a.Task) time.Time {
	if t.Status.Timestamp == nil {
		return time.Time{}
	}
	return *t.Status.Timestamp
}

// all 은 디렉터리의 기록을 이름 차례로 읽는다(읽지 못한 것은 건너뛴다).
func (s *Store) all() []*record {
	names, _ := filepath.Glob(filepath.Join(s.dir, "*.json"))
	slices.Sort(names)
	var out []*record
	for _, n := range names {
		id := strings.TrimSuffix(filepath.Base(n), ".json")
		if r, err := s.read(a2a.TaskID(id)); err == nil {
			out = append(out, r)
		}
	}
	return out
}

// region: recover
// Recover 는 띄울 때 한 번: 실행기 없이 남은 SUBMITTED·WORKING 을
// FAILED 로 닫는다.
func (s *Store) Recover() error {
	for _, r := range s.all() {
		t := r.Task
		st := t.Status.State
		if st != a2a.TaskStateSubmitted && st != a2a.TaskStateWorking {
			continue
		}
		msg := a2a.NewMessageForTask(a2a.MessageRoleAgent, t,
			a2a.NewTextPart("서버가 다시 시작되어 끊겼습니다"))
		msg.ID = "recover-" + string(t.ID)
		now := time.Now()
		t.Status = a2a.TaskStatus{
			State: a2a.TaskStateFailed, Message: msg, Timestamp: &now}
		r.Version++
		if err := s.write(r); err != nil {
			return err
		}
		fmt.Printf("[복구] %s %s → FAILED\n", t.ID,
			strings.TrimPrefix(string(st), "TASK_STATE_"))
	}
	return nil
}

// endregion
