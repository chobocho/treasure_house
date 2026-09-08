package minipuppy

import (
	"fmt"
	"io/fs"
	"os"
	"path/filepath"
	"sort"
	"strings"
)

var skipDirs = map[string]bool{
	".git": true, "__pycache__": true, "node_modules": true, ".venv": true,
	"venv": true, "dist": true, "build": true, ".idea": true,
}

const maxReadBytes = 400_000

// Workspace 는 실행 문맥 — 작업 뿌리와 승인 정책, 서브에이전트 깊이.
type Workspace struct {
	Root     string
	Yolo     bool
	Approver func(action, rel string) bool
	Depth    int
	Writes   []string
}

func NewWorkspace(root string) (*Workspace, error) {
	abs, err := filepath.Abs(root)
	if err != nil {
		return nil, err
	}
	real, err := filepath.EvalSymlinks(abs)
	if err != nil {
		real = abs
	}
	return &Workspace{Root: real}, nil
}

// Resolve 는 뿌리 안쪽 경로만 돌려준다. 밖이면 오류.
//
// 심볼릭 링크까지 풀어서 본다 — 링크를 걸어 두고 그 링크를 읽어 달라고 하면
// 문자열 검사만으로는 못 막는다.
func (w *Workspace) Resolve(rel string) (string, error) {
	if strings.TrimSpace(rel) == "" {
		return "", fmt.Errorf("경로가 비었다.")
	}
	p := rel
	if !filepath.IsAbs(p) {
		p = filepath.Join(w.Root, rel)
	}
	p = filepath.Clean(p)
	if real, err := filepath.EvalSymlinks(p); err == nil {
		p = real
	}
	if p != w.Root && !strings.HasPrefix(p, w.Root+string(filepath.Separator)) {
		return "", fmt.Errorf("작업 뿌리 밖은 만질 수 없다: %s", rel)
	}
	return p, nil
}

func (w *Workspace) Approve(action, path string) error {
	if w.Yolo {
		return nil
	}
	rel, _ := filepath.Rel(w.Root, path)
	if w.Approver == nil {
		return fmt.Errorf("쓰기 승인이 필요한데 승인 창구가 없다: %s", rel)
	}
	if !w.Approver(action, rel) {
		return fmt.Errorf("사용자가 거절했다: %s %s", action, rel)
	}
	return nil
}

func (w *Workspace) rel(p string) string {
	r, err := filepath.Rel(w.Root, p)
	if err != nil {
		return p
	}
	return filepath.ToSlash(r)
}

type listArgs struct {
	Path       string `json:"path" desc:"뿌리 기준 상대 경로"`
	Pattern    string `json:"pattern" desc:"파일 이름 glob (예: *.go)"`
	MaxResults int    `json:"max_results" desc:"최대 몇 개까지"`
}

type readArgs struct {
	Path  string `json:"path" desc:"뿌리 기준 상대 경로" required:"true"`
	Start int    `json:"start" desc:"시작 행 (1부터)"`
	End   int    `json:"end" desc:"끝 행 (0 이면 끝까지)"`
}

type writeArgs struct {
	Path    string `json:"path" desc:"뿌리 기준 상대 경로" required:"true"`
	Content string `json:"content" desc:"파일 전체 내용" required:"true"`
}

type editArgs struct {
	Path    string `json:"path" desc:"뿌리 기준 상대 경로" required:"true"`
	Find    string `json:"find" desc:"찾을 문자열 (그대로, 정규식 아님)" required:"true"`
	Replace string `json:"replace" desc:"바꿀 문자열" required:"true"`
	Count   int    `json:"count" desc:"몇 군데까지. 0 이면 전부"`
}

type grepArgs struct {
	Needle     string `json:"needle" desc:"찾을 문자열" required:"true"`
	Pattern    string `json:"pattern" desc:"파일 이름 glob"`
	MaxResults int    `json:"max_results" desc:"최대 몇 줄까지"`
}

// RegisterFileTools 는 파일 도구 다섯을 등록한다.
func RegisterFileTools(r *Registry) {
	Register(r, "list_files", "디렉터리를 재귀로 훑어 파일 목록을 준다.",
		func(w *Workspace, a listArgs) (string, error) {
			if a.Path == "" {
				a.Path = "."
			}
			if a.Pattern == "" {
				a.Pattern = "*"
			}
			if a.MaxResults <= 0 {
				a.MaxResults = 200
			}
			base, err := w.Resolve(a.Path)
			if err != nil {
				return "", err
			}
			var out []string
			err = filepath.WalkDir(base, func(p string, d fs.DirEntry, err error) error {
				if err != nil {
					return nil
				}
				if d.IsDir() {
					if skipDirs[d.Name()] {
						return filepath.SkipDir
					}
					return nil
				}
				if ok, _ := filepath.Match(a.Pattern, d.Name()); !ok {
					return nil
				}
				info, _ := d.Info()
				size := int64(0)
				if info != nil {
					size = info.Size()
				}
				out = append(out, fmt.Sprintf("%8d  %s", size, w.rel(p)))
				if len(out) >= a.MaxResults {
					return filepath.SkipAll
				}
				return nil
			})
			if err != nil {
				return "", err
			}
			if len(out) == 0 {
				return "(없음)", nil
			}
			return strings.Join(out, "\n"), nil
		})

	Register(r, "read_file", "파일을 행 번호를 붙여 읽는다.",
		func(w *Workspace, a readArgs) (string, error) {
			p, err := w.Resolve(a.Path)
			if err != nil {
				return "", err
			}
			st, err := os.Stat(p)
			if err != nil || st.IsDir() {
				return "", fmt.Errorf("파일이 아니다: %s", a.Path)
			}
			if st.Size() > maxReadBytes {
				return "", fmt.Errorf("너무 크다(%d바이트). start/end 로 잘라 읽어라.", st.Size())
			}
			raw, err := os.ReadFile(p)
			if err != nil {
				return "", err
			}
			lines := strings.Split(strings.ReplaceAll(string(raw), "\r\n", "\n"), "\n")
			if n := len(lines); n > 0 && lines[n-1] == "" {
				lines = lines[:n-1]
			}
			lo, hi := a.Start, a.End
			if lo < 1 {
				lo = 1
			}
			if hi <= 0 || hi > len(lines) {
				hi = len(lines)
			}
			if lo > hi {
				return "(빈 범위)", nil
			}
			width := len(fmt.Sprint(hi))
			var b strings.Builder
			for i := lo; i <= hi; i++ {
				fmt.Fprintf(&b, "%*d  %s\n", width, i, lines[i-1])
			}
			return strings.TrimRight(b.String(), "\n"), nil
		})

	Register(r, "write_file", "파일을 새로 쓴다(있으면 통째로 덮는다).",
		func(w *Workspace, a writeArgs) (string, error) {
			p, err := w.Resolve(a.Path)
			if err != nil {
				return "", err
			}
			action := "새로 만들기"
			if _, err := os.Stat(p); err == nil {
				action = "덮어쓰기"
			}
			if err := w.Approve(action, p); err != nil {
				return "", err
			}
			if err := AtomicWriteFile(p, []byte(a.Content)); err != nil {
				return "", err
			}
			w.Writes = append(w.Writes, w.rel(p))
			return fmt.Sprintf("%s 에 %d자 썼다.", a.Path, len([]rune(a.Content))), nil
		})

	Register(r, "edit_file", "파일에서 찾은 문자열을 바꾼다. 유일하지 않으면 거절한다.",
		func(w *Workspace, a editArgs) (string, error) {
			p, err := w.Resolve(a.Path)
			if err != nil {
				return "", err
			}
			raw, err := os.ReadFile(p)
			if err != nil {
				return "", fmt.Errorf("파일이 아니다: %s", a.Path)
			}
			text := string(raw)
			hits := strings.Count(text, a.Find)
			if hits == 0 {
				return "", fmt.Errorf("찾는 문자열이 없다. 공백·들여쓰기까지 그대로 줘야 한다.")
			}
			if a.Count <= 1 && hits > 1 {
				return "", fmt.Errorf("%d군데에서 걸린다. 앞뒤를 더 붙여 유일하게 만들거나 count 를 지정해라.", hits)
			}
			if err := w.Approve("고치기", p); err != nil {
				return "", err
			}
			n := a.Count
			if n <= 0 {
				n = hits
			}
			if err := AtomicWriteFile(p, []byte(strings.Replace(text, a.Find, a.Replace, n))); err != nil {
				return "", err
			}
			w.Writes = append(w.Writes, w.rel(p))
			return fmt.Sprintf("%s 에서 %d군데 바꿨다.", a.Path, n), nil
		})

	Register(r, "grep", "작업 뿌리 아래에서 문자열이 든 줄을 찾는다.",
		func(w *Workspace, a grepArgs) (string, error) {
			if a.Pattern == "" {
				a.Pattern = "*"
			}
			if a.MaxResults <= 0 {
				a.MaxResults = 100
			}
			var out []string
			_ = filepath.WalkDir(w.Root, func(p string, d fs.DirEntry, err error) error {
				if err != nil {
					return nil
				}
				if d.IsDir() {
					if skipDirs[d.Name()] {
						return filepath.SkipDir
					}
					return nil
				}
				if ok, _ := filepath.Match(a.Pattern, d.Name()); !ok {
					return nil
				}
				info, _ := d.Info()
				if info != nil && info.Size() > maxReadBytes {
					return nil
				}
				raw, err := os.ReadFile(p)
				if err != nil {
					return nil
				}
				for i, line := range strings.Split(string(raw), "\n") {
					if strings.Contains(line, a.Needle) {
						t := strings.TrimSpace(line)
						if len([]rune(t)) > 200 {
							t = string([]rune(t)[:200])
						}
						out = append(out, fmt.Sprintf("%s:%d: %s", w.rel(p), i+1, t))
						if len(out) >= a.MaxResults {
							return filepath.SkipAll
						}
					}
				}
				return nil
			})
			if len(out) == 0 {
				return "(없음)", nil
			}
			sort.SliceStable(out, func(i, j int) bool { return out[i] < out[j] })
			return strings.Join(out, "\n"), nil
		})
}
