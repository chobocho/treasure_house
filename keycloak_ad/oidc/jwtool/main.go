package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"net/http"
	"os"
	"strings"
	"time"

	"treasure/keycloak_ad/oidc/jwt"
)

const usage = `쓰는 법:
  jwtool decode [토큰]
  jwtool verify -jwks <주소나 파일> [-iss ...] [-aud ...] [토큰]

토큰을 빼면 표준 입력에서 읽는다:
  curl -s ... | jq -r .id_token | jwtool decode
`

func main() {
	if len(os.Args) < 2 {
		fmt.Fprint(os.Stderr, usage)
		os.Exit(2)
	}
	var err error
	switch os.Args[1] {
	case "decode":
		err = cmdDecode(os.Args[2:])
	case "verify":
		err = cmdVerify(os.Args[2:])
	default:
		fmt.Fprint(os.Stderr, usage)
		os.Exit(2)
	}
	if err != nil {
		fmt.Fprintf(os.Stderr, "jwtool: %v\n", err)
		os.Exit(1)
	}
}

func cmdDecode(args []string) error {
	fs := flag.NewFlagSet("decode", flag.ExitOnError)
	nowFlag := fs.String("now", "",
		"이 시각 기준으로 남은 시간을 센다 (RFC3339, 캡처용)")
	fs.Parse(args)
	tok, err := readToken(fs.Args())
	if err != nil {
		return err
	}
	now, err := clockAt(*nowFlag)
	if err != nil {
		return err
	}
	return decode(os.Stdout, tok, now)
}

// clockAt 은 깃발이 비면 진짜 시계를, 아니면 못 박은 시각을 준다.
// 덱의 캡처를 두 번 떠서 견주려면 "3분 전" 같은 말이 고정돼야 한다.
func clockAt(s string) (time.Time, error) {
	if s == "" {
		return time.Now(), nil
	}
	t, err := time.Parse(time.RFC3339, s)
	if err != nil {
		return time.Time{}, fmt.Errorf("-now: %w", err)
	}
	return t, nil
}

func cmdVerify(args []string) error {
	fs := flag.NewFlagSet("verify", flag.ExitOnError)
	jwks := fs.String("jwks", "", "JWKS 주소나 파일")
	iss := fs.String("iss", "", "기대하는 발급자")
	aud := fs.String("aud", "", "기대하는 대상 (client_id)")
	nowFlag := fs.String("now", "",
		"이 시각 기준으로 본다 (RFC3339, 캡처용)")
	fs.Parse(args)
	if *jwks == "" {
		return fmt.Errorf("-jwks 가 필요하다 " +
			"(안내문의 jwks_uri 를 그대로 주면 된다)")
	}
	tok, err := readToken(fs.Args())
	if err != nil {
		return err
	}
	ks, err := loadKeySet(*jwks)
	if err != nil {
		return err
	}
	now, err := clockAt(*nowFlag)
	if err != nil {
		return err
	}
	return verify(os.Stdout, tok, ks, verifyOptions{
		Issuer: *iss, Audience: *aud, Now: now})
}

// readToken 은 인자로 받거나, 없으면 표준 입력에서 읽는다.
// 파이프로 이어 쓰기 위해서다 — 토큰은 손으로 옮겨 적기엔 너무 길다.
func readToken(args []string) (string, error) {
	if len(args) > 0 {
		return strings.TrimSpace(args[0]), nil
	}
	b, err := io.ReadAll(os.Stdin)
	if err != nil {
		return "", err
	}
	s := strings.TrimSpace(string(b))
	if s == "" {
		return "", fmt.Errorf("토큰이 없다")
	}
	return s, nil
}

// loadKeySet 은 http(s) 면 받아 오고, 아니면 파일로 읽는다.
func loadKeySet(src string) (*jwt.KeySet, error) {
	var raw []byte
	if strings.HasPrefix(src, "http://") ||
		strings.HasPrefix(src, "https://") {
		res, err := http.Get(src)
		if err != nil {
			return nil, err
		}
		defer res.Body.Close()
		if res.StatusCode != http.StatusOK {
			return nil, fmt.Errorf("%s → %d", src, res.StatusCode)
		}
		raw, err = io.ReadAll(res.Body)
		if err != nil {
			return nil, err
		}
	} else {
		var err error
		if raw, err = os.ReadFile(src); err != nil {
			return nil, err
		}
	}
	var ks jwt.KeySet
	if err := json.Unmarshal(raw, &ks); err != nil {
		return nil, fmt.Errorf("JWKS 를 못 읽었다: %w", err)
	}
	if len(ks.Keys) == 0 {
		return nil, fmt.Errorf("JWKS 에 열쇠가 없다")
	}
	return &ks, nil
}
