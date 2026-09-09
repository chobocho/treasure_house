// Package minipuppy — Code Puppy 의 뼈대를 Go 로 다시 만든 것.
//
// 파이썬판(mini_puppy/)과 층 구성은 같다. 다른 것은 언어가 강제하는 부분이다:
//   - 파이썬은 타입 힌트를 읽어 도구 스키마를 만든다. Go 는 reflect 로 구조체를
//     읽는다 — 대신 **컴파일 때** 인자 모양이 고정된다.
//   - 파이썬은 CancelToken(threading.Event) 으로 멈춘다. Go 는 context.Context.
//   - 파이썬 버스는 락과 리스트다. Go 버스는 채널이다.
package minipuppy

import (
	"fmt"
	"strings"
	"sync"
	"time"
)

// Kind 는 사건 종류. 렌더러가 이 값으로 색과 모양을 고른다.
type Kind string

const (
	KindUser    Kind = "user"
	KindAgent   Kind = "agent"
	KindTool    Kind = "tool"
	KindToolOut Kind = "tool_out"
	KindInfo    Kind = "info"
	KindWarn    Kind = "warn"
	KindError   Kind = "error"
	KindSystem  Kind = "system"
)

var icons = map[Kind]string{
	KindUser: "▶", KindAgent: "🐶", KindTool: "⚙", KindToolOut: "  ",
	KindInfo: "ℹ", KindWarn: "⚠", KindError: "✖", KindSystem: "·",
}

// Message 는 버스를 흐르는 사건 하나.
type Message struct {
	Kind Kind
	Text string
	Meta map[string]string
	At   time.Time
}

// Sink 는 사건을 받아 그리는 쪽.
type Sink func(Message)

// Bus 는 여러 고루틴이 넣고 붙은 싱크들이 순서대로 받는다.
//
// 파이썬판과 같은 계약: 싱크 하나가 패닉을 내도 나머지는 계속 받는다.
// 렌더러가 죽었다고 에이전트를 멈추면 안 되기 때문.
type Bus struct {
	mu         sync.RWMutex
	sinks      []Sink
	log        []Message
	sinkPanics []string
}

func NewBus(sinks ...Sink) *Bus {
	b := &Bus{}
	for _, s := range sinks {
		b.Subscribe(s)
	}
	return b
}

func (b *Bus) Subscribe(s Sink) {
	b.mu.Lock()
	defer b.mu.Unlock()
	b.sinks = append(b.sinks, s)
}

func (b *Bus) Emit(kind Kind, text string, kv ...string) Message {
	msg := Message{Kind: kind, Text: text, At: time.Now()}
	if len(kv) >= 2 {
		msg.Meta = map[string]string{}
		for i := 0; i+1 < len(kv); i += 2 {
			msg.Meta[kv[i]] = kv[i+1]
		}
	}
	b.mu.Lock()
	b.log = append(b.log, msg)
	sinks := make([]Sink, len(b.sinks))
	copy(sinks, b.sinks)
	b.mu.Unlock()
	for _, s := range sinks {
		b.deliver(s, msg)
	}
	return msg
}

// deliver 는 싱크의 패닉을 여기서 삼킨다.
func (b *Bus) deliver(s Sink, msg Message) {
	defer func() {
		if r := recover(); r != nil {
			b.mu.Lock()
			b.sinkPanics = append(b.sinkPanics, fmt.Sprint(r))
			b.mu.Unlock()
		}
	}()
	s(msg)
}

func (b *Bus) Infof(format string, a ...any)  { b.Emit(KindInfo, fmt.Sprintf(format, a...)) }
func (b *Bus) Warnf(format string, a ...any)  { b.Emit(KindWarn, fmt.Sprintf(format, a...)) }
func (b *Bus) Errorf(format string, a ...any) { b.Emit(KindError, fmt.Sprintf(format, a...)) }

func (b *Bus) Log() []Message {
	b.mu.RLock()
	defer b.mu.RUnlock()
	out := make([]Message, len(b.log))
	copy(out, b.log)
	return out
}

func (b *Bus) SinkPanics() []string {
	b.mu.RLock()
	defer b.mu.RUnlock()
	return append([]string(nil), b.sinkPanics...)
}

// Collector 는 시험용 싱크. 받은 것을 쌓아 둔다.
type Collector struct {
	mu   sync.Mutex
	Msgs []Message
	Only map[Kind]bool
}

func NewCollector(only ...Kind) *Collector {
	c := &Collector{}
	if len(only) > 0 {
		c.Only = map[Kind]bool{}
		for _, k := range only {
			c.Only[k] = true
		}
	}
	return c
}

func (c *Collector) Sink(m Message) {
	if c.Only != nil && !c.Only[m.Kind] {
		return
	}
	c.mu.Lock()
	defer c.mu.Unlock()
	c.Msgs = append(c.Msgs, m)
}

func (c *Collector) Kinds() []Kind {
	c.mu.Lock()
	defer c.mu.Unlock()
	out := make([]Kind, len(c.Msgs))
	for i, m := range c.Msgs {
		out[i] = m.Kind
	}
	return out
}

func (c *Collector) Last() Message {
	c.mu.Lock()
	defer c.mu.Unlock()
	if len(c.Msgs) == 0 {
		return Message{}
	}
	return c.Msgs[len(c.Msgs)-1]
}

// ConsoleSink 는 가장 단순한 렌더러. 여러 줄은 같은 자리에서 이어 그린다.
func ConsoleSink(m Message) {
	icon := icons[m.Kind]
	if icon == "" {
		icon = " "
	}
	pad := strings.Repeat(" ", len([]rune(icon))+1)
	for i, line := range strings.Split(m.Text, "\n") {
		if i == 0 {
			fmt.Println(icon + " " + line)
		} else {
			fmt.Println(pad + line)
		}
	}
}
