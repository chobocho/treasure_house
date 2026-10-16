// Package workshop 는 보물상사 워크숍 시나리오의 업무 규칙이다.
// 세 언어가 같은 규칙을 구현한다(deck/SCENARIO.md).
package workshop

import (
	"encoding/json"
	"errors"
	"os"
	"path/filepath"
	"sync"
)

type Venue struct {
	ID                  string   `json:"id"`
	Name                string   `json:"name"`
	Capacity            int      `json:"capacity"`
	RoomSize            int      `json:"roomSize"`
	PricePerPersonNight int      `json:"pricePerPersonNight"`
	Closed              []string `json:"closed"`
}

type Menu struct {
	Type       string `json:"type"`
	ID         string `json:"id"`
	Name       string `json:"name"`
	Price      int    `json:"price"`
	Vegetarian bool   `json:"vegetarian"`
}

type Bus struct {
	ID          string `json:"id"`
	Seats       int    `json:"seats"`
	PricePerDay int    `json:"pricePerDay"`
	Plate       string `json:"plate"`
}

type Data struct {
	Venues            []Venue        `json:"venues"`
	Menus             []Menu         `json:"menus"`
	DefaultCaps       map[string]int `json:"defaultCaps"`
	Buses             []Bus          `json:"buses"`
	BusSteps          []string       `json:"busSteps"`
	ApprovalThreshold int            `json:"approvalThreshold"`
}

type OAuthClient struct {
	ClientID     string   `json:"clientId"`
	ClientSecret string   `json:"clientSecret"`
	Scopes       []string `json:"scopes"`
}

// fixturesDir 는 현재 디렉터리에서 위로 올라가며 fixtures/ 를 찾는다.
// 시험(ex/go/workshop)과 실행(ex/go) 어느 쪽에서 불러도 같은 파일을
// 읽게 하려는 것이다.
func fixturesDir() (string, error) {
	dir, err := os.Getwd()
	if err != nil {
		return "", err
	}
	for {
		p := filepath.Join(dir, "fixtures")
		_, err := os.Stat(filepath.Join(p, "workshop.json"))
		if err == nil {
			return p, nil
		}
		up := filepath.Dir(dir)
		if up == dir {
			return "", errors.New("fixtures/workshop.json 을 찾지 못함")
		}
		dir = up
	}
}

func load(name string, v any) error {
	dir, err := fixturesDir()
	if err != nil {
		return err
	}
	b, err := os.ReadFile(filepath.Join(dir, name))
	if err != nil {
		return err
	}
	return json.Unmarshal(b, v)
}

// Workshop 은 처음 부를 때 한 번만 읽는다. 자료가 없으면 프로그램이
// 할 수 있는 일이 없으므로 panic 으로 멈춘다.
var Workshop = sync.OnceValue(func() *Data {
	var d Data
	if err := load("workshop.json", &d); err != nil {
		panic(err)
	}
	return &d
})

// Clients 는 로컬 OAuth2 발급기가 아는 클라이언트 목록이다.
var Clients = sync.OnceValue(func() []OAuthClient {
	var d struct {
		Clients []OAuthClient `json:"clients"`
	}
	if err := load("clients.json", &d); err != nil {
		panic(err)
	}
	return d.Clients
})
