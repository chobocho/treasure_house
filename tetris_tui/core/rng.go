package core

// Rng 는 xorshift32. 난수의 품질보다 **결정론과 이식성**이 중요해서 이걸 쓴다.
//
// C++ 코어는 -nostdlib 라 rand() 가 없었고, 그래서 13줄짜리 xorshift 를 직접 썼다.
// Go 에는 math/rand 가 있지만 여기서 쓰면 안 된다 — 같은 시드에서 C++ 과 같은
// 조각 순서가 나와야 골든 트레이스가 성립하기 때문이다. 알고리즘까지 이식한다.
type Rng struct {
	s uint32
}

// 시드 0 을 대신하는 값. xorshift 는 상태가 0 이면 영원히 0 이라
// 조각이 언제나 같은 하나만 나오는 판이 된다. 황금비의 32비트 근삿값을 쓴다.
const defaultSeed = 0x9E3779B9

// NewRng 는 시드로 난수원을 만든다. 시드 0 은 defaultSeed 로 바뀐다.
func NewRng(seed uint32) *Rng {
	if seed == 0 {
		seed = defaultSeed
	}
	return &Rng{s: seed}
}

// Next 는 다음 32비트 난수. C++ 의 rnd() 와 같은 수열이다.
//
// 세 번의 시프트-XOR 만으로 주기 2³²−1 을 얻는다. 통계적으로 훌륭한 난수는
// 아니지만, 조각 일곱 개를 섞는 데는 차고 넘친다.
func (r *Rng) Next() uint32 {
	r.s ^= r.s << 13
	r.s ^= r.s >> 17
	r.s ^= r.s << 5
	return r.s
}

// IntN 은 [0, n) 의 값.
//
// 나머지 연산은 편향이 있다(2³² 가 n 으로 안 나눠떨어지면 앞쪽 값이 조금 더 자주 나온다).
// Go 의 math/rand 는 이걸 없애지만 여기서는 **일부러 그대로 둔다** —
// 편향까지 같아야 C++ 과 같은 순열이 나오기 때문이다.
func (r *Rng) IntN(n int) int {
	if n <= 0 {
		return 0
	}
	return int(r.Next() % uint32(n))
}

// Bag 은 7-bag 랜더마이저.
//
// 7종을 한 봉지에 넣고 섞어서 하나씩 꺼낸다. "S/Z만 10번 연속" 같은 사고가
// 원천적으로 불가능해진다. 같은 조각 사이의 최악 대기는 12개다
// (봉지 앞에서 나오고 다음 봉지 뒤에서 나오는 경우).
type Bag struct {
	r     *Rng
	items [PieceCount]int
	idx   int
}

// NewBag 은 "이미 다 쓴 봉지" 상태로 시작한다 — 첫 Pull 이 곧바로 새 봉지를 섞는다.
// C++ 의 ts_init 이 bag_idx = 7 로 두는 것과 같다.
// 이 한 줄이 없으면 첫 일곱 조각이 I,J,L,O,S,T,Z 순서로 고정된다.
func NewBag(r *Rng) *Bag {
	return &Bag{r: r, idx: PieceCount}
}

// Pull 은 다음 조각 하나. 봉지가 비면 새로 섞는다.
func (b *Bag) Pull() int {
	if b.idx >= PieceCount {
		b.refill()
	}
	p := b.items[b.idx]
	b.idx++
	return p
}

// refill 은 Fisher-Yates 로 봉지를 섞는다.
//
// 뒤에서부터 도는 방향까지 원본과 같다 — 앞에서부터 돌면 같은 난수열에서
// 다른 순열이 나온다. "같은 알고리즘"이 아니라 "같은 결과"가 목표다.
//
// O(7) 시간, 할당 없음.
func (b *Bag) refill() {
	for i := 0; i < PieceCount; i++ {
		b.items[i] = i
	}
	for i := PieceCount - 1; i > 0; i-- {
		j := b.r.IntN(i + 1)
		b.items[i], b.items[j] = b.items[j], b.items[i]
	}
	b.idx = 0
}
