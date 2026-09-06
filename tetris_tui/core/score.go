package core

// GravityMs[level] = 한 칸 떨어지는 데 걸리는 밀리초.
//
// 가이드라인 공식은 (0.8 − 0.007×(level−1))^(level−1) 초/칸 이다.
// C++ 코어는 -nostdlib 라 pow() 를 쓸 수 없어 미리 계산해 굳혔다.
// Go 에는 math.Pow 가 있지만 여기서도 표를 그대로 쓴다 —
// 부동소수점 반올림이 한 밀리초라도 다르면 골든 트레이스가 갈라지기 때문이다.
// 부수 효과로 런타임 의존성 0, 조회 O(1) 이라는 이득도 그대로 따라온다.
var GravityMs = [21]uint16{
	1000,                                    // [0] 미사용(레벨은 1부터)
	1000, 793, 618, 473, 355, 262, 190, 135, // 레벨 1~8
	94, 64, 43, 28, 18, 11, 7, 4, // 레벨 9~16
	3, 2, 1, 1, // 레벨 17~20
}

// MaxLevel 은 중력표의 마지막 레벨. 이 위로는 올라가지 않는다.
const MaxLevel = 20

// Gravity 는 레벨의 낙하 간격(ms). 범위를 벗어난 레벨은 양 끝으로 자른다.
func Gravity(level int) int {
	if level < 1 {
		level = 1
	}
	if level > MaxLevel {
		level = MaxLevel
	}
	return int(GravityMs[level])
}

// LineScore 는 지운 줄 수와 T스핀 종류에 대한 기본 점수, 그리고
// 이번 클리어가 "어려운 클리어"인지를 돌려준다.
//
// 가이드라인 점수표 그대로다:
//
//	싱글 100 / 더블 300 / 트리플 500 / 테트리스 800   (×레벨)
//	T스핀 0/1/2/3줄 = 400/800/1200/1600
//	미니 T스핀 = 100/200/400
//
// "어려운 클리어"의 정의(테트리스 또는 T스핀)가 Back-to-Back 과 공격표 양쪽에서
// 같은 뜻으로 쓰여야 해서, 판정을 여기 한 곳에만 둔다.
func LineScore(n, tspin int) (base int, difficult bool) {
	if n < 0 {
		n = 0
	}
	if n > 4 {
		n = 4
	}
	switch tspin {
	case TSpinFull:
		return [5]int{400, 800, 1200, 1600, 1600}[n], n > 0
	case TSpinMini:
		return [5]int{100, 200, 400, 400, 400}[n], n > 0
	default:
		return [5]int{0, 100, 300, 500, 800}[n], n == 4
	}
}

// LevelFor 는 누적 줄 수에 대응하는 레벨. 10줄마다 하나씩 오르고 20에서 멈춘다.
func LevelFor(lines int) int {
	lv := 1 + lines/10
	if lv > MaxLevel {
		lv = MaxLevel
	}
	return lv
}
