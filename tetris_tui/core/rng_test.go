package core

import "testing"

// xorshift32 의 첫 몇 값은 C++ 원본에서 직접 뽑아 왔다.
// "같은 알고리즘을 썼다"가 아니라 "같은 수가 나온다"를 확인해야
// 골든 트레이스의 조각 순서가 맞을 수 있다.
//
//	x ^= x<<13; x ^= x>>17; x ^= x<<5;
func TestXorshiftSequence(t *testing.T) {
	r := NewRng(1)
	want := []uint32{270369, 67634689, 2647435461, 307599695, 2398689233}
	for i, w := range want {
		if got := r.Next(); got != w {
			t.Fatalf("%d번째 난수가 %d — %d 를 기대했다", i, got, w)
		}
	}
}

// 시드 0 은 함정이다. xorshift 는 상태가 0 이면 영원히 0 을 낸다 —
// 조각이 언제나 같은 하나만 나오는 판이 된다. 원본처럼 황금비 상수로 갈아탄다.
func TestZeroSeedIsReplaced(t *testing.T) {
	if NewRng(0).Next() == 0 {
		t.Fatal("시드 0 에서 0 이 나왔다 — 수열이 죽었다")
	}
	if NewRng(0).Next() != NewRng(0x9E3779B9).Next() {
		t.Error("시드 0 이 0x9E3779B9 로 바뀌지 않았다")
	}
}

// 경계 시드. u32 의 끝값에서도 수열이 돌아야 한다.
func TestMaxSeedRuns(t *testing.T) {
	r := NewRng(0xFFFFFFFF)
	seen := map[uint32]bool{}
	for i := 0; i < 100; i++ {
		seen[r.Next()] = true
	}
	if len(seen) < 90 {
		t.Errorf("100번 뽑았는데 서로 다른 값이 %d개뿐이다", len(seen))
	}
}

func TestIntNRange(t *testing.T) {
	r := NewRng(12345)
	for i := 0; i < 1000; i++ {
		if v := r.IntN(W); v < 0 || v >= W {
			t.Fatalf("IntN(%d) 이 %d 를 냈다", W, v)
		}
	}
}

// 7-bag 의 계약: 연속한 7개는 반드시 7종이 한 번씩이다.
func TestBagIsAPermutationOfSeven(t *testing.T) {
	b := NewBag(NewRng(7))
	for round := 0; round < 50; round++ {
		var seen [PieceCount]int
		for i := 0; i < PieceCount; i++ {
			p := b.Pull()
			if p < 0 || p >= PieceCount {
				t.Fatalf("봉지가 %d 를 냈다", p)
			}
			seen[p]++
		}
		for p, n := range seen {
			if n != 1 {
				t.Fatalf("%d번째 봉지에서 %s 가 %d번 나왔다", round, PieceNames[p], n)
			}
		}
	}
}

// 같은 시드면 같은 순서. 다른 시드면 다른 순서.
func TestBagIsDeterministic(t *testing.T) {
	pull := func(seed uint32, n int) []int {
		b := NewBag(NewRng(seed))
		out := make([]int, n)
		for i := range out {
			out[i] = b.Pull()
		}
		return out
	}
	a, b := pull(42, 21), pull(42, 21)
	for i := range a {
		if a[i] != b[i] {
			t.Fatalf("같은 시드인데 %d번째가 다르다: %d vs %d", i, a[i], b[i])
		}
	}
	c := pull(43, 21)
	same := true
	for i := range a {
		if a[i] != c[i] {
			same = false
			break
		}
	}
	if same {
		t.Error("시드가 달라도 순서가 같다")
	}
}

// 봉지는 "이미 다 쓴 상태"로 시작해야 한다 — 첫 Pull 이 곧바로 섞는다.
// 안 그러면 첫 봉지가 0..6 순서 그대로 나와서 첫 일곱 조각이 늘 같다.
func TestFirstBagIsShuffled(t *testing.T) {
	b := NewBag(NewRng(1))
	first := make([]int, PieceCount)
	for i := range first {
		first[i] = b.Pull()
	}
	inOrder := true
	for i, p := range first {
		if p != i {
			inOrder = false
			break
		}
	}
	if inOrder {
		t.Error("첫 봉지가 0,1,2,3,4,5,6 그대로다 — 섞이지 않았다")
	}
}
