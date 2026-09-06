package ai

import "treasure/tetris_tui/core"

// Features 는 판 하나에서 특징 8개를 뽑는다.
//
//	b      : 줄을 지운 *뒤*의 판
//	lines  : 이 수로 지워진 줄 수
//	landH  : 조각 맨 아랫줄의 바닥 기준 높이 (바닥줄 = 1)
//
// lines 와 landH 는 판만 봐서는 알 수 없다(줄이 지워지고 나면 흔적이 사라진다).
// 그래서 호출자가 넘겨 준다.
//
// O(H×W) 시간, 할당 없음. 한 수를 고르는 데 이 함수가 100번 가까이 불리므로
// 열 높이를 한 번만 재고 나머지를 전부 그 배열에서 파생시킨다.
func Features(b *core.Board, lines, landH int) [FCount]float32 {
	var h [core.W]int
	holes := 0
	for x := 0; x < core.W; x++ {
		y := 0
		for y < core.H && b.At(x, y) == 0 {
			y++
		}
		h[x] = core.H - y // 열 높이 = 가장 높은 블록까지
		for yy := y + 1; yy < core.H; yy++ {
			if b.At(x, yy) == 0 {
				holes++ // 덮인 빈칸
			}
		}
	}

	agg, bump, wells := 0, 0, 0
	for x := 0; x < core.W; x++ {
		agg += h[x]
	}
	for x := 0; x+1 < core.W; x++ {
		d := h[x] - h[x+1]
		if d < 0 {
			d = -d
		}
		bump += d
	}
	for x := 0; x < core.W; x++ {
		// 양옆(벽은 천장 높이로 친다)보다 낮게 파인 만큼이 우물이다.
		// 벽을 천장으로 쳐야 "벽에 붙은 1칸 우물"이 우물로 잡힌다.
		l, r := core.H, core.H
		if x > 0 {
			l = h[x-1]
		}
		if x < core.W-1 {
			r = h[x+1]
		}
		m := l
		if r < m {
			m = r
		}
		if d := m - h[x]; d > 0 {
			wells += d * (d + 1) / 2 // 깊이 d 의 비용 1+2+…+d
		}
	}

	// 행/열 전이: 채움↔빈칸이 뒤집히는 횟수. 벽과 바닥은 "채워진 것"으로 센다.
	// 울퉁불퉁하고 구멍 많은 판일수록 커진다 — 높이만으로는 안 보이는 결을 잡아낸다.
	// (Dellacherie 의 고전적인 특징 둘)
	rowt := 0
	for y := 0; y < core.H; y++ {
		prev := 1 // 왼쪽 벽
		for x := 0; x < core.W; x++ {
			c := 0
			if b.At(x, y) != 0 {
				c = 1
			}
			if c != prev {
				rowt++
			}
			prev = c
		}
		if prev == 0 {
			rowt++ // 오른쪽 벽
		}
	}
	colt := 0
	for x := 0; x < core.W; x++ {
		prev := 0 // 천장 위는 비어 있다
		for y := 0; y < core.H; y++ {
			c := 0
			if b.At(x, y) != 0 {
				c = 1
			}
			if c != prev {
				colt++
			}
			prev = c
		}
		if prev == 0 {
			colt++ // 바닥
		}
	}

	return [FCount]float32{
		FLines: float32(lines),
		FAgg:   float32(agg),
		FHoles: float32(holes),
		FBump:  float32(bump),
		FWells: float32(wells),
		FRowT:  float32(rowt),
		FColT:  float32(colt),
		FLand:  float32(landH),
	}
}

// Score 는 가중치와 특징의 내적.
//
// float32 로 누적하는 것이 핵심이다. float64 로 더하면 값이 미세하게 달라지고,
// 동점 근처에서 argmax 가 다른 후보를 골라 그때부터 판이 통째로 갈라진다.
// "더 정확한 계산"이 아니라 "다른 AI"가 되는 것이다.
//
// float32(...) 명시 변환이 왜 필요한가 — 이 프로젝트에서 실제로 밟은 함정이다.
//
//	s += w[i] * f[i]              // 이렇게 쓰면 arm64 에서 FMADD 명령 하나로 합쳐진다
//	s += float32(w[i] * f[i])     // 이렇게 써야 곱셈 결과가 float32 로 한 번 반올림된다
//
// Go 사양은 여러 부동소수점 연산을 융합(FMA)해도 된다고 허용하고, arm64 컴파일러는
// 실제로 그렇게 한다. 융합하면 중간 반올림이 한 번 사라져서 **더 정확한** 값이 나오는데,
// 하필 그게 C++ wasm 정답지와 다른 값이다. 정답지의 −153.53359985 가 우리 쪽에서는
// −153.53358 이 나왔다(1 ULP 차이). 여기서는 "정확함"이 아니라 "같음"이 목표다.
func Score(w Weights, f [FCount]float32) float32 {
	var s float32
	for i := 0; i < FCount; i++ {
		s += float32(w[i] * f[i])
	}
	return s
}
