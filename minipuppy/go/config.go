package minipuppy

import (
	"bufio"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strconv"
	"strings"
	"sync"
)

// Defaults 는 층 3 — 코드에 박힌 기본값.
var Defaults = map[string]string{
	"model":                "scripted",
	"agent":                "minipuppy",
	"yolo_mode":            "false",
	"compaction_threshold": "0.75",
	"protected_tokens":     "2000",
	"context_window":       "16000",
	"max_tool_output":      "8000",
	"command_timeout":      "30",
	"max_subagent_depth":   "3",
	"max_steps":            "20",
}

// Config 는 세 겹으로 쌓고 위에서부터 읽는다.
//
//  1. 환경변수  MINIPUPPY_<KEY 대문자>
//  2. 설정 파일 <dir>/puppy.cfg
//  3. Defaults
//
// 규칙 하나만 지키면 된다: 위층이 아래층을 가린다.
type Config struct {
	Dir string
	Env map[string]string

	mu    sync.Mutex
	cache map[string]string
	stamp string
}

func NewConfig(dir string, env map[string]string) *Config {
	if dir == "" {
		home, _ := os.UserHomeDir()
		dir = filepath.Join(home, ".minipuppy")
	}
	if env == nil {
		env = map[string]string{}
		for _, kv := range os.Environ() {
			if i := strings.IndexByte(kv, '='); i > 0 {
				env[kv[:i]] = kv[i+1:]
			}
		}
	}
	return &Config{Dir: dir, Env: env}
}

func (c *Config) Path() string { return filepath.Join(c.Dir, "puppy.cfg") }

func (c *Config) envKey(key string) string {
	return "MINIPUPPY_" + strings.ToUpper(key)
}

// fileLayer 는 mtime+size 로 캐시한다. REPL 이 매 턴 설정을 읽는데 매번
// 디스크를 때리면 느리고, 캐시만 하면 사용자가 파일을 고쳐도 반영이 안 된다.
func (c *Config) fileLayer() map[string]string {
	c.mu.Lock()
	defer c.mu.Unlock()
	st, err := os.Stat(c.Path())
	stamp := ""
	if err == nil {
		stamp = fmt.Sprintf("%d-%d", st.ModTime().UnixNano(), st.Size())
	}
	if c.cache != nil && stamp == c.stamp {
		return c.cache
	}
	got := map[string]string{}
	if f, err := os.Open(c.Path()); err == nil {
		sc := bufio.NewScanner(f)
		for sc.Scan() {
			line := strings.TrimSpace(sc.Text())
			if line == "" || strings.HasPrefix(line, "#") ||
				strings.HasPrefix(line, "[") {
				continue
			}
			k, v, ok := strings.Cut(line, "=")
			if !ok {
				continue
			}
			got[strings.TrimSpace(k)] = strings.TrimSpace(v)
		}
		f.Close()
	}
	c.cache, c.stamp = got, stamp
	return got
}

func (c *Config) Get(key string) string {
	if v, ok := c.Env[c.envKey(key)]; ok {
		return v
	}
	if v, ok := c.fileLayer()[key]; ok {
		return v
	}
	return Defaults[key]
}

// Source 는 이 값이 어느 층에서 왔는지.
func (c *Config) Source(key string) string {
	if _, ok := c.Env[c.envKey(key)]; ok {
		return "env"
	}
	if _, ok := c.fileLayer()[key]; ok {
		return "file"
	}
	if _, ok := Defaults[key]; ok {
		return "default"
	}
	return "none"
}

func (c *Config) Bool(key string) bool {
	switch strings.ToLower(strings.TrimSpace(c.Get(key))) {
	case "1", "true", "yes", "on", "y":
		return true
	}
	return false
}

func (c *Config) Int(key string) int {
	n, err := strconv.Atoi(strings.TrimSpace(c.Get(key)))
	if err != nil {
		f, ferr := strconv.ParseFloat(strings.TrimSpace(c.Get(key)), 64)
		if ferr != nil {
			return 0
		}
		return int(f)
	}
	return n
}

func (c *Config) Float(key string) float64 {
	f, err := strconv.ParseFloat(strings.TrimSpace(c.Get(key)), 64)
	if err != nil {
		return 0
	}
	return f
}

// Set 은 파일 층에만 쓴다. 환경변수가 덮고 있으면 Get 은 여전히 환경변수를
// 준다 — 의도한 것이다. 껍데기가 아니라 진짜 우선순위를 보여 줘야 한다.
func (c *Config) Set(key, value string) error {
	layer := map[string]string{}
	for k, v := range c.fileLayer() {
		layer[k] = v
	}
	layer[key] = value
	keys := make([]string, 0, len(layer))
	for k := range layer {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	var b strings.Builder
	b.WriteString("[puppy]\n")
	for _, k := range keys {
		fmt.Fprintf(&b, "%s = %s\n", k, layer[k])
	}
	if err := AtomicWriteFile(c.Path(), []byte(b.String())); err != nil {
		return err
	}
	c.mu.Lock()
	c.stamp = "" // 다음 읽기에서 다시 읽게
	c.mu.Unlock()
	return nil
}

func (c *Config) All() map[string]string {
	out := map[string]string{}
	for k, v := range Defaults {
		out[k] = v
	}
	for k, v := range c.fileLayer() {
		out[k] = v
	}
	for k := range out {
		if v, ok := c.Env[c.envKey(k)]; ok {
			out[k] = v
		}
	}
	return out
}

func (c *Config) SessionsDir() string { return filepath.Join(c.Dir, "sessions") }
func (c *Config) AgentsDir() string   { return filepath.Join(c.Dir, "agents") }

// LimitsFrom 은 설정에서 루프가 지킬 숫자들을 뽑는다.
func LimitsFrom(c *Config) Limits {
	l := DefaultLimits()
	if v := c.Int("context_window"); v > 0 {
		l.ContextWindow = v
	}
	if v := c.Float("compaction_threshold"); v > 0 {
		l.CompactionThreshold = v
	}
	if v := c.Int("protected_tokens"); v > 0 {
		l.ProtectedTokens = v
	}
	if v := c.Int("max_tool_output"); v > 0 {
		l.MaxToolOutput = v
	}
	if v := c.Int("max_steps"); v > 0 {
		l.MaxSteps = v
	}
	return l
}
