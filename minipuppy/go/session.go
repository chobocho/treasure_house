package minipuppy

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"time"
)

// SchemaVersion 은 세션 파일 형식 번호. 올릴 때마다 Migrate 에 한 단계를 더한다.
const SchemaVersion = 2

// AtomicWriteFile 은 반쯤 쓰다 만 파일을 절대 남기지 않는다.
//
// 같은 디렉터리에 임시 파일로 다 쓰고, Sync 로 디스크에 내린 뒤,
// os.Rename 으로 갈아 끼운다. 같은 볼륨 안에서 Rename 은 원자적이다
// (POSIX rename(2), Windows MoveFileEx). 노트북이 절전되거나 Ctrl-C 가
// 들어와도 디스크 위의 파일은 "이전" 아니면 "이후"다. 중간은 없다.
func AtomicWriteFile(path string, data []byte) error {
	dir := filepath.Dir(path)
	if err := os.MkdirAll(dir, 0o755); err != nil {
		return err
	}
	tmp, err := os.CreateTemp(dir, filepath.Base(path)+".*.tmp")
	if err != nil {
		return err
	}
	name := tmp.Name()
	cleanup := func() { tmp.Close(); os.Remove(name) }
	if _, err := tmp.Write(data); err != nil {
		cleanup()
		return err
	}
	if err := tmp.Sync(); err != nil { // 내용이 진짜 디스크에 닿게
		cleanup()
		return err
	}
	if err := tmp.Close(); err != nil {
		os.Remove(name)
		return err
	}
	if err := os.Rename(name, path); err != nil { // 여기서부터 새 내용
		os.Remove(name)
		return err
	}
	syncDir(dir)
	return nil
}

// syncDir 은 디렉터리 엔트리까지 내려 Rename 이 살아남게 한다.
// Windows 에서는 디렉터리를 열 수 없어 조용히 넘어간다.
func syncDir(dir string) {
	f, err := os.Open(dir)
	if err != nil {
		return
	}
	defer f.Close()
	_ = f.Sync()
}

func AtomicWriteJSON(path string, v any) error {
	b, err := json.MarshalIndent(v, "", "  ")
	if err != nil {
		return err
	}
	return AtomicWriteFile(path, append(b, '\n'))
}

// Session 은 한 번의 대화.
type Session struct {
	ID       string `json:"id"`
	Agent    string `json:"agent"`
	Title    string `json:"title"`
	Created  int64  `json:"created"`
	Updated  int64  `json:"updated"`
	Messages []Msg  `json:"messages"`
	Version  int    `json:"version"`
}

func NewSession(agent string) *Session {
	now := time.Now().Unix()
	return &Session{
		ID:    fmt.Sprintf("%x", time.Now().UnixNano())[:12],
		Agent: agent, Created: now, Updated: now, Version: SchemaVersion,
	}
}

// Migrate 는 옛 세션 파일을 지금 형식으로 끌어올린다.
//
// 형식을 바꾸면 사용자의 지난 세션이 전부 안 열린다. 버전을 적어 두고
// 한 단계씩 올리는 것 말고 안전한 방법이 없다.
func Migrate(raw map[string]any) (*Session, error) {
	version := 1
	if v, ok := raw["version"].(float64); ok {
		version = int(v)
	}
	if version < 2 {
		// v1 은 messages 가 ["문자열", ...] 였다. v2 는 {role, content, ...}.
		var fixed []any
		for _, m := range toSlice(raw["messages"]) {
			switch g := m.(type) {
			case string:
				fixed = append(fixed, map[string]any{"role": "user", "content": g})
			case map[string]any:
				fixed = append(fixed, g)
			}
		}
		raw["messages"] = fixed
		if _, ok := raw["agent"]; !ok {
			raw["agent"] = "minipuppy"
		}
		version = 2
	}
	raw["version"] = version
	b, err := json.Marshal(raw)
	if err != nil {
		return nil, err
	}
	var s Session
	if err := json.Unmarshal(b, &s); err != nil {
		return nil, err
	}
	return &s, nil
}

func toSlice(v any) []any {
	if s, ok := v.([]any); ok {
		return s
	}
	return nil
}

// Store 는 세션 파일 보관소.
type Store struct{ Dir string }

func (s Store) path(id string) string { return filepath.Join(s.Dir, id+".json") }

func (s Store) Save(sess *Session) error {
	sess.Updated = time.Now().Unix()
	return AtomicWriteJSON(s.path(sess.ID), sess)
}

func (s Store) Load(id string) (*Session, error) {
	raw, err := os.ReadFile(s.path(id))
	if err != nil {
		return nil, err
	}
	var m map[string]any
	if err := json.Unmarshal(raw, &m); err != nil {
		return nil, err
	}
	return Migrate(m)
}

// List 는 최신순. 알아볼 수 없는 파일은 조용히 건너뛴다.
func (s Store) List() []*Session {
	entries, err := os.ReadDir(s.Dir)
	if err != nil {
		return nil
	}
	var out []*Session
	for _, e := range entries {
		if e.IsDir() || !strings.HasSuffix(e.Name(), ".json") {
			continue
		}
		got, err := s.Load(strings.TrimSuffix(e.Name(), ".json"))
		if err != nil {
			continue
		}
		out = append(out, got)
	}
	sort.SliceStable(out, func(i, j int) bool { return out[i].Updated > out[j].Updated })
	return out
}

func (s Store) Delete(id string) bool { return os.Remove(s.path(id)) == nil }
