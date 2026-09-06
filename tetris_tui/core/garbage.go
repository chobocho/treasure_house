package core

// 대전 규칙: 공격표와 가비지.
//
// 줄을 지우면 상대 필드 바닥에 그만큼의 "가비지"가 밀려 올라간다.
// 표는 현대 대전 테트리스의 사실상 표준을 따랐다.
//
//	싱글 0 / 더블 1 / 트리플 2 / 테트리스 4
//	T스핀 싱글 2 / 더블 4 / 트리플 6, 미니 T스핀 0 / 미니 더블 1
//	Back-to-Back +1, 콤보 보너스 표, 퍼펙트 클리어 +10
//
// 싱글이 0 인 게 이 표의 핵심이다 — 한 줄씩 지우는 플레이는 공격이 되지 않는다.
// 그래서 "쌓아 두었다가 한 번에 지우는" 대전 특유의 리듬이 생긴다.
var (
	attackPlain = [5]int{0, 0, 1, 2, 4} // -, 싱글, 더블, 트리플, 테트리스
	attackTSpin = [5]int{0, 2, 4, 6, 6} // 정식 T스핀
	attackMini  = [5]int{0, 0, 1, 1, 1} // 미니 T스핀
)

// ComboAttack[c] = 콤보 c 일 때 더해지는 줄 수. 12 에서 천장을 친다.
var ComboAttack = [13]int{0, 0, 1, 1, 1, 2, 2, 3, 3, 4, 4, 4, 5}

// Attack 은 이번 락이 상대에게 보낼 줄 수를 계산한다(상쇄 전).
//
// b2bBefore 는 이번 락이 B2B 상태를 덮어쓰기 **전**의 값이어야 한다.
// 이 순서를 틀리면 테트리스 연속에서 +1 이 한 박자씩 밀린다 — 실제로 밟기 쉬운 함정이라
// 인자 이름에 before 를 박아 뒀다.
func Attack(n, tspin int, b2bBefore bool, combo int, perfect bool) int {
	if n <= 0 {
		return 0
	}
	if n > 4 {
		n = 4
	}
	var atk int
	switch tspin {
	case TSpinFull:
		atk = attackTSpin[n]
	case TSpinMini:
		atk = attackMini[n]
	default:
		atk = attackPlain[n]
	}

	// "어려운 클리어"의 정의는 점수 규칙과 같다 — 테트리스 또는 T스핀.
	if _, difficult := LineScore(n, tspin); difficult && b2bBefore {
		atk++
	}

	c := combo
	if c < 0 {
		c = 0
	}
	if c > len(ComboAttack)-1 {
		c = len(ComboAttack) - 1
	}
	atk += ComboAttack[c]

	if perfect {
		atk += 10
	}
	return atk
}
