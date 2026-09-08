// jwtool — 토큰 한 장을 눈으로 보는 도구.
//
// 하는 일은 딱 두 가지고, **그 둘이 다르다는 것**이 요점이다.
//
//	jwtool decode <토큰>              읽기만 한다. 아무나 할 수 있다
//	jwtool verify -jwks <주소> <토큰>  믿어도 되는지 확인한다
//
// 토큰의 내용은 암호가 아니라 base64url 이다. 그래서 decode 는 열쇠
// 없이 되고, 서명이 망가진 토큰도 읽어 낸다. "읽었다" 와 "믿는다" 를
// 같은 것으로 착각하는 순간 4부에서 배운 것이 전부 무너진다.
//
// 5부에서 진짜 Keycloak 이 준 토큰에도 같은 명령을 그대로 쓴다.
package main

import (
	"encoding/json"
	"fmt"
	"io"
	"sort"
	"strings"
	"time"
	"unicode"

	"treasure/keycloak_ad/oidc/jwt"
)

type verifyOptions struct {
	Issuer   string
	Audience string
	Now      time.Time
}

// ── 폭 맞추기 ────────────────────────────────────────────────────────

// cells 는 화면에서 차지하는 칸 수다. 한글은 한 글자가 두 칸이라
// len() 으로 세면 표가 어긋난다 — 폴더블 접힌 화면에서 특히.
func cells(s string) int {
	n := 0
	for _, r := range s {
		wide := unicode.Is(unicode.Hangul, r) ||
			unicode.Is(unicode.Han, r) ||
			unicode.Is(unicode.Hiragana, r) ||
			unicode.Is(unicode.Katakana, r) ||
			(r >= 0xFF00 && r <= 0xFF60)
		if r >= 0x1100 && wide {
			n += 2
			continue
		}
		n++
	}
	return n
}

const lineMax = 76

// wrapValue 는 긴 값을 접는다. 이어지는 줄은 라벨 칸만큼 들여쓴다.
//
// 라벨 폭을 밖에서 받는 이유: preferred_username 처럼 긴 이름이 하나만
// 섞여도 고정 폭으로는 칸이 어긋난다 — 접힌 화면에서 특히 눈에 띈다.
func wrapValue(w io.Writer, label, value string, labelW int) {
	indent := 2 + labelW + 1
	pad := strings.Repeat(" ", indent)
	room := lineMax - indent
	head := fmt.Sprintf("  %-*s ", labelW, label)
	first := true
	for cells(value) > room {
		cut, n := 0, 0
		for i, r := range value {
			c := 1
			if cells(string(r)) == 2 {
				c = 2
			}
			if n+c > room {
				break
			}
			n += c
			cut = i + len(string(r))
		}
		if first {
			fmt.Fprintf(w, "%s%s\n", head, value[:cut])
			first = false
		} else {
			fmt.Fprintf(w, "%s%s\n", pad, value[:cut])
		}
		value = value[cut:]
	}
	if first {
		fmt.Fprintf(w, "%s%s\n", head, value)
		return
	}
	fmt.Fprintf(w, "%s%s\n", pad, value)
}

// ── 시각 ─────────────────────────────────────────────────────────────

// 토큰의 시각은 1970년부터 센 초다(RFC 7519 §2 NumericDate).
// 사람은 그 숫자를 못 읽으므로 옆에 풀어 적는다.
func whenSay(sec int64, now time.Time) string {
	t := time.Unix(sec, 0).UTC()
	d := t.Sub(now)
	return fmt.Sprintf("%d (%s · %s)", sec,
		t.Format("2006-01-02 15:04:05 UTC"), agoSay(d))
}

func agoSay(d time.Duration) string {
	future := d >= 0
	if !future {
		d = -d
	}
	var unit string
	switch {
	case d < 30*time.Second:
		return "방금"
	case d < time.Hour:
		unit = fmt.Sprintf("%d분", int(d.Minutes()))
	case d < 24*time.Hour:
		unit = fmt.Sprintf("%d시간", int(d.Hours()))
	default:
		unit = fmt.Sprintf("%d일", int(d.Hours())/24)
	}
	if future {
		return unit + " 뒤"
	}
	return unit + " 전"
}

// ── decode ───────────────────────────────────────────────────────────

// 먼저 보여 줄 클레임 순서. RFC 7519 §4.1 이 정한 것부터, 그 다음
// OIDC 가 정한 것. 나머지는 이름 순으로 뒤에 붙인다.
var claimOrder = []string{
	"iss", "sub", "aud", "exp", "nbf", "iat", "jti", "nonce", "azp",
	"typ", "preferred_username", "email", "name", "groups",
}

var timeClaims = map[string]bool{"exp": true, "nbf": true, "iat": true,
	"auth_time": true}

func decode(w io.Writer, token string, now time.Time) error {
	parts := strings.Split(token, ".")
	if len(parts) != 3 {
		return fmt.Errorf("조각이 %d개다 — 토큰은 세 조각이어야 한다",
			len(parts))
	}
	head, err := rawJSON(parts[0])
	if err != nil {
		return fmt.Errorf("머리: %w", err)
	}
	body, err := rawJSON(parts[1])
	if err != nil {
		return fmt.Errorf("내용: %w", err)
	}
	sig, err := jwt.B64URLDecode(parts[2])
	if err != nil {
		return fmt.Errorf("서명: %w", err)
	}

	fmt.Fprintln(w, "머리 (header) — 어떤 방법으로 서명했나")
	printMap(w, head, now)
	fmt.Fprintln(w)
	fmt.Fprintln(w,
		"내용 (payload) — 발급자가 그렇다고 **주장**하는 것")
	printMap(w, body, now)
	fmt.Fprintln(w)
	fmt.Fprintf(w, "서명 %d바이트 — 확인하지 않았다.\n", len(sig))
	fmt.Fprintln(w, "  이 내용을 믿어도 되는지는 verify 가 답한다.")
	return nil
}

func rawJSON(part string) (map[string]any, error) {
	b, err := jwt.B64URLDecode(part)
	if err != nil {
		return nil, err
	}
	var m map[string]any
	if err := json.Unmarshal(b, &m); err != nil {
		return nil, err
	}
	return m, nil
}

func printMap(w io.Writer, m map[string]any, now time.Time) {
	labelW := 6
	for k := range m {
		if len(k) > labelW {
			labelW = len(k)
		}
	}
	if labelW > 20 {
		labelW = 20
	}
	seen := map[string]bool{}
	for _, k := range claimOrder {
		if v, ok := m[k]; ok {
			seen[k] = true
			wrapValue(w, k, showValue(k, v, now), labelW)
		}
	}
	rest := make([]string, 0, len(m))
	for k := range m {
		if !seen[k] {
			rest = append(rest, k)
		}
	}
	sort.Strings(rest)
	for _, k := range rest {
		wrapValue(w, k, showValue(k, m[k], now), labelW)
	}
}

func showValue(key string, v any, now time.Time) string {
	if f, ok := v.(float64); ok {
		if timeClaims[key] {
			return whenSay(int64(f), now)
		}
		return fmt.Sprintf("%d", int64(f))
	}
	if s, ok := v.(string); ok {
		return s
	}
	b, err := json.Marshal(v)
	if err != nil {
		return fmt.Sprint(v)
	}
	return string(b)
}

// ── verify ───────────────────────────────────────────────────────────

// verify 는 세 가지를 차례로 본다. 하나라도 어긋나면 거기서 멈춘다.
//
//  1. 서명   이 발급자의 개인키로 만든 것인가 (JWKS 의 공개키로 확인)
//  2. 기한   아직 살아 있는가
//  3. 대상   나에게, 저 발급자가 준 것인가
//
// 1번만 보고 통과시키는 코드가 흔하다. 서명이 맞는 **남의 토큰**은
// 세상에 얼마든지 있다 — 그래서 2·3번이 있다.
func verify(w io.Writer, token string, ks *jwt.KeySet,
	opt verifyOptions) error {
	now := opt.Now
	if now.IsZero() {
		now = time.Now()
	}

	h, c, err := jwt.Verify(token, ks)
	if err != nil {
		return fmt.Errorf("서명 확인 실패: %w", err)
	}
	fmt.Fprintf(w, "서명   맞다 (%s, kid=%s)\n", h.Alg, h.Kid)

	// 기한을 따로 먼저 본다. 가장 흔한 실패라서 이유를 또렷이 적는다.
	if c.Exp == 0 {
		return fmt.Errorf(
			"기한(exp)이 없다 — 영원한 토큰은 받지 않는다")
	}
	if !now.Before(time.Unix(c.Exp, 0)) {
		return fmt.Errorf("기한이 지났다: exp %s",
			whenSay(c.Exp, now))
	}
	fmt.Fprintf(w, "기한   %s\n", whenSay(c.Exp, now))

	if err := c.Validate(jwt.Options{
		Issuer: opt.Issuer, Audience: opt.Audience, Now: now,
	}); err != nil {
		return fmt.Errorf("내용 확인 실패: %w", err)
	}
	fmt.Fprintf(w, "발급자 %s\n", c.Iss)
	fmt.Fprintf(w, "대상   %s\n", c.Aud)
	fmt.Fprintf(w, "사람   %s (%s)\n", c.PreferredUsername, c.Sub)
	if len(c.Groups) > 0 {
		fmt.Fprintf(w, "그룹   %s\n", strings.Join(c.Groups, ", "))
	}
	fmt.Fprintln(w, "→ 이 토큰은 믿어도 된다.")
	return nil
}
