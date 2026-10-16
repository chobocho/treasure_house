// 워크숍 규칙 — 입력과 자료만으로 답이 정해지는 순수 함수들.
// A2A 와는 무관한 '업무 로직'이다. 에이전트는 이 함수를 부르고 결과를
// A2A 메시지·아티팩트로 감싸기만 한다. 결과 모양은 골든 파일이 정한다.
package workshop

import (
	"fmt"
	"regexp"
	"slices"
	"strconv"
	"strings"
	"time"
)

const (
	badSize = "인원과 박 수는 1 이상이어야 합니다"
	badVeg  = "채식 인원은 0명 이상, 전체 인원 이하여야 합니다"
)

// Fail 은 규칙이 요청을 받아들이지 못한 이유다.
type Fail struct {
	OK     bool   `json:"ok"`
	Reason string `json:"reason"`
}

func fail(reason string) *Fail {
	return &Fail{OK: false, Reason: reason}
}

func ceilDiv(a, b int) int { return (a + b - 1) / b }

type LodgingRequest struct {
	Date      string `json:"date"`
	Nights    int    `json:"nights"`
	Headcount int    `json:"headcount"`
}

type LodgingQuote struct {
	OK        bool   `json:"ok"`
	VenueID   string `json:"venueId"`
	VenueName string `json:"venueName"`
	Rooms     int    `json:"rooms"`
	Nights    int    `json:"nights"`
	Headcount int    `json:"headcount"`
	Total     int    `json:"total"`
}

// ChooseLodging 은 숙박 가능한 곳 중 총액이 가장 싼 곳을 고른다.
// O(숙소 수 × 박 수).
func ChooseLodging(r LodgingRequest) (LodgingQuote, *Fail) {
	hc, nights := r.Headcount, r.Nights
	if hc < 1 || nights < 1 {
		return LodgingQuote{}, fail(badSize)
	}
	first, err := time.Parse(time.DateOnly, r.Date)
	if err != nil {
		msg := fmt.Sprintf("날짜 형식: %s", r.Date)
		return LodgingQuote{}, fail(msg)
	}
	var best *LodgingQuote
	for _, v := range Workshop().Venues {
		if v.Capacity < hc || closedAny(v, first, nights) {
			continue
		}
		total := hc * v.PricePerPersonNight * nights
		// 같은 값이면 id 가 작은 쪽 — 언어마다 정렬이 달라도 답이 같게.
		if best == nil || total < best.Total ||
			(total == best.Total && v.ID < best.VenueID) {
			best = &LodgingQuote{
				OK: true, VenueID: v.ID, VenueName: v.Name,
				Rooms:  ceilDiv(hc, v.RoomSize),
				Nights: nights, Headcount: hc, Total: total,
			}
		}
	}
	if best == nil {
		return LodgingQuote{}, fail("가능한 숙소가 없습니다")
	}
	return *best, nil
}

func closedAny(v Venue, first time.Time, nights int) bool {
	for i := range nights {
		d := first.AddDate(0, 0, i).Format(time.DateOnly)
		if slices.Contains(v.Closed, d) {
			return true
		}
	}
	return false
}

// MealSlots: n박이면 저녁·아침을 n번, 마지막 날 점심 한 번 — 2n+1 끼.
func MealSlots(nights int) []string {
	var s []string
	for i := 1; i <= nights; i++ {
		s = append(s,
			fmt.Sprintf("day%d-dinner", i),
			fmt.Sprintf("day%d-breakfast", i+1))
	}
	return append(s, fmt.Sprintf("day%d-lunch", nights+1))
}

type MealsRequest struct {
	Nights      int            `json:"nights"`
	Headcount   int            `json:"headcount"`
	Vegetarians int            `json:"vegetarians"`
	Caps        map[string]int `json:"caps,omitempty"`
}

type Choice struct {
	ID    string `json:"id"`
	Name  string `json:"name"`
	Price int    `json:"price"`
	Count int    `json:"count"`
}

// Slot 의 한쪽에 먹을 사람이 없으면 nil — JSON 으로는 null.
type Slot struct {
	Slot       string  `json:"slot"`
	Regular    *Choice `json:"regular"`
	Vegetarian *Choice `json:"vegetarian"`
}

type MealPlan struct {
	OK    bool   `json:"ok"`
	Slots []Slot `json:"slots"`
	Total int    `json:"total"`
}

// pick 은 상한 이하에서 가장 비싼 메뉴를 고른다.
// 같은 값이면 id 가 작은 쪽.
func pick(kind string, veg bool, limit int) *Menu {
	var best *Menu
	for i, m := range Workshop().Menus {
		if m.Type != kind || m.Vegetarian != veg || m.Price > limit {
			continue
		}
		if best == nil || m.Price > best.Price ||
			(m.Price == best.Price && m.ID < best.ID) {
			best = &Workshop().Menus[i]
		}
	}
	return best
}

// PlanMeals 는 끼니마다 일반식·채식을 고른다. O(끼니 수 × 메뉴 수).
func PlanMeals(r MealsRequest) (MealPlan, *Fail) {
	hc, nights, veg := r.Headcount, r.Nights, r.Vegetarians
	if hc < 1 || nights < 1 {
		return MealPlan{}, fail(badSize)
	}
	if veg < 0 || veg > hc {
		return MealPlan{}, fail(badVeg)
	}
	caps := map[string]int{}
	for k, v := range Workshop().DefaultCaps {
		caps[k] = v
	}
	for k, v := range r.Caps {
		caps[k] = v
	}
	plan := MealPlan{OK: true, Slots: []Slot{}}
	for _, slot := range MealSlots(nights) {
		kind := strings.SplitN(slot, "-", 2)[1]
		row := Slot{Slot: slot}
		sides := []struct {
			dst   **Choice
			count int
			veg   bool
		}{{&row.Regular, hc - veg, false}, {&row.Vegetarian, veg, true}}
		for _, s := range sides {
			if s.count == 0 {
				continue // 먹을 사람이 없으면 고르지 않는다
			}
			m := pick(kind, s.veg, caps[kind])
			if m == nil {
				msg := "예산 안에 맞는 메뉴가 없습니다"
				return MealPlan{}, fail(msg)
			}
			*s.dst = &Choice{m.ID, m.Name, m.Price, s.count}
			plan.Total += m.Price * s.count
		}
		plan.Slots = append(plan.Slots, row)
	}
	return plan, nil
}

type BusRequest struct {
	Headcount int `json:"headcount"`
	Nights    int `json:"nights"`
}

type Vehicle struct {
	ID    string `json:"id"`
	Count int    `json:"count"`
}

type BusPlan struct {
	OK         bool      `json:"ok"`
	Vehicles   []Vehicle `json:"vehicles"`
	Days       int       `json:"days"`
	CostPerDay int       `json:"costPerDay"`
	Total      int       `json:"total"`
}

func bus(id string) Bus {
	for _, b := range Workshop().Buses {
		if b.ID == id {
			return b
		}
	}
	panic("버스 자료에 " + id + " 없음")
}

// ChooseBuses 는 45인승 a대 + 25인승 b대로 좌석을 채우는 가장 싼
// 조합을 고른다. a 를 모두 시도한다 — O(h/45), 워크숍 규모에선 충분.
// 같은 값이면 차가 적은 쪽, 그다음 45인승이 많은 쪽.
func ChooseBuses(r BusRequest) (BusPlan, *Fail) {
	hc, nights := r.Headcount, r.Nights
	if hc < 1 || nights < 1 {
		return BusPlan{}, fail(badSize)
	}
	big, small := bus("bus45"), bus("bus25")
	bestCost, bestA, bestB := -1, 0, 0
	for a := 0; a <= ceilDiv(hc, big.Seats); a++ {
		b := ceilDiv(max(0, hc-a*big.Seats), small.Seats)
		cost := a*big.PricePerDay + b*small.PricePerDay
		better := bestCost < 0 || cost < bestCost ||
			(cost == bestCost && a+b < bestA+bestB) ||
			(cost == bestCost && a+b == bestA+bestB && a > bestA)
		if better {
			bestCost, bestA, bestB = cost, a, b
		}
	}
	var vs []Vehicle
	if bestA > 0 {
		vs = append(vs, Vehicle{"bus45", bestA})
	}
	if bestB > 0 {
		vs = append(vs, Vehicle{"bus25", bestB})
	}
	days := nights + 1
	return BusPlan{true, vs, days, bestCost, bestCost * days}, nil
}

type Item struct {
	Name   string `json:"name"`
	Amount int    `json:"amount"`
}

type SettleRequest struct {
	Items    []Item `json:"items"`
	Budget   int    `json:"budget"`
	Approved bool   `json:"approved"`
}

// SettleResult 의 Budget·Remaining 은 completed 일 때만 있다.
// 0 원도 값이므로 omitempty 를 쓰려면 포인터여야 한다.
type SettleResult struct {
	OK        bool   `json:"ok"`
	Status    string `json:"status"`
	Total     int    `json:"total"`
	Budget    *int   `json:"budget,omitempty"`
	Remaining *int   `json:"remaining,omitempty"`
}

type OverBudget struct {
	OK     bool   `json:"ok"`
	Reason string `json:"reason"`
	Over   int    `json:"over"`
}

// Settle 은 예산 초과를 먼저 보고, 그다음 결재 필요 여부를 본다.
func Settle(r SettleRequest) (SettleResult, *OverBudget) {
	total := 0
	for _, it := range r.Items {
		total += it.Amount
	}
	if total > r.Budget {
		return SettleResult{}, &OverBudget{false, "예산을 초과합니다",
			total - r.Budget}
	}
	if total > Workshop().ApprovalThreshold && !r.Approved {
		return SettleResult{OK: true, Status: "auth-required",
			Total: total}, nil
	}
	budget, remaining := r.Budget, r.Budget-total
	return SettleResult{
		true, "completed", total, &budget, &remaining,
	}, nil
}

// Go 의 RE2 에는 뒤보기(lookbehind)가 없다. 세 언어가 같은 정규식을
// 쓰려고, 채식 인원을 먼저 찾아 지운 다음 전체 인원을 찾는다.
var (
	reVeg       = regexp.MustCompile(`채식\s*(\d+)명`)
	reDate      = regexp.MustCompile(`(\d{4}-\d{2}-\d{2})`)
	reNights    = regexp.MustCompile(`(\d+)박`)
	reHeadcount = regexp.MustCompile(`(\d+)명`)
	reBudget    = regexp.MustCompile(`예산\s*([\d,]+)원`)
	reDepart    = regexp.MustCompile(`출발\s*(\S+)`)
)

type Parsed struct {
	OK          bool    `json:"ok"`
	Date        string  `json:"date"`
	Nights      int     `json:"nights"`
	Headcount   int     `json:"headcount"`
	Vegetarians int     `json:"vegetarians"`
	Budget      *int    `json:"budget"`
	Depart      *string `json:"depart"`
}

type Missing struct {
	OK      bool     `json:"ok"`
	Missing []string `json:"missing"`
}

// ParseRequest 는 자유 문장에서 날짜·박 수·인원·채식·예산·출발지를
// 뽑는다. 빠진 필수 항목이 있으면 두 번째 값으로 알려 준다.
func ParseRequest(text string) (Parsed, *Missing) {
	p := Parsed{OK: true}
	rest := text
	if loc := reVeg.FindStringSubmatchIndex(text); loc != nil {
		p.Vegetarians, _ = strconv.Atoi(text[loc[2]:loc[3]])
		rest = text[:loc[0]] + text[loc[1]:] // 첫 번째만 지운다
	}
	var miss []string
	date := reDate.FindStringSubmatch(rest)
	nights := reNights.FindStringSubmatch(rest)
	head := reHeadcount.FindStringSubmatch(rest)
	for _, f := range []struct {
		name string
		m    []string
	}{{"date", date}, {"nights", nights}, {"headcount", head}} {
		if f.m == nil {
			miss = append(miss, f.name)
		}
	}
	if miss != nil {
		return Parsed{}, &Missing{false, miss}
	}
	p.Date = date[1]
	p.Nights, _ = strconv.Atoi(nights[1])
	p.Headcount, _ = strconv.Atoi(head[1])
	if m := reBudget.FindStringSubmatch(rest); m != nil {
		b, _ := strconv.Atoi(strings.ReplaceAll(m[1], ",", ""))
		p.Budget = &b
	}
	if m := reDepart.FindStringSubmatch(rest); m != nil {
		p.Depart = &m[1]
	}
	return p, nil
}
