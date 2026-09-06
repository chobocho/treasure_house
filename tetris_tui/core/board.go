package core

// Board 는 굳은 블록만 담는 판이다. 0 = 빈칸, 1~7 = 조각 색, 8 = 가비지.
//
// 배열 하나로 두는 이유. [][]uint8 은 줄마다 포인터를 따라가야 하고 캐시에서 흩어진다.
// 240바이트짜리 연속 배열이면 판 전체가 캐시 한 줄에 가깝게 들어오고,
// 줄을 끌어내리는 연산이 copy() 한 번으로 끝난다.
type Board [H * W]uint8

// At 은 (x, y) 의 값. 범위 밖은 0 을 돌려준다 — 호출자가 매번 검사하지 않게.
func (b *Board) At(x, y int) uint8 {
	if x < 0 || x >= W || y < 0 || y >= H {
		return 0
	}
	return b[y*W+x]
}

// Set 은 (x, y) 를 칠한다. 범위 밖은 조용히 무시한다.
func (b *Board) Set(x, y int, v uint8) {
	if x < 0 || x >= W || y < 0 || y >= H {
		return
	}
	b[y*W+x] = v
}

// Collide 는 (piece, rot) 모양을 (px, py) 에 놓았을 때 겹치는지 본다.
//   - 좌우/바닥 밖 → 충돌
//   - 천장 위(y < 0) → 충돌 아님 (조각이 위로 삐져나오는 건 합법이다)
//   - 굳은 블록 → 충돌
//
// O(16) 시간, 할당 없음. 코어에서 가장 자주 불리는 함수라 비트마스크를 직접 훑는다.
func (b *Board) Collide(piece, rot, px, py int) bool {
	m := Shapes[piece][rot&3]
	for i := 0; i < 16; i++ {
		if m&(1<<uint(i)) == 0 {
			continue
		}
		bx := px + (i & 3)
		by := py + (i >> 2)
		if bx < 0 || bx >= W || by >= H {
			return true
		}
		if by < 0 {
			continue
		}
		if b[by*W+bx] != 0 {
			return true
		}
	}
	return false
}

// Filled 는 T스핀의 코너 판정용. 벽과 바닥은 "막힌 것"으로, 천장 위는 "빈 것"으로 센다.
// Collide 와 경계 취급이 다르다는 점이 핵심이다 — 벽에 붙은 T스핀이 성립하는 이유가 이것이다.
func (b *Board) Filled(x, y int) bool {
	if x < 0 || x >= W || y >= H {
		return true
	}
	if y < 0 {
		return false
	}
	return b[y*W+x] != 0
}

// Place 는 조각을 판에 굳힌다. 색은 piece+1.
func (b *Board) Place(piece, rot, x, y int) {
	m := Shapes[piece][rot&3]
	for i := 0; i < 16; i++ {
		if m&(1<<uint(i)) == 0 {
			continue
		}
		b.Set(x+(i&3), y+(i>>2), uint8(piece+1))
	}
}

// DropY 는 (piece, rot, x) 를 y 에서 아래로 떨어뜨렸을 때 멈추는 y.
func (b *Board) DropY(piece, rot, x, y int) int {
	for !b.Collide(piece, rot, x, y+1) {
		y++
	}
	return y
}

// ClearLines 는 꽉 찬 줄을 지우고 위를 끌어내린다.
// 지운 줄 수와, 보이는 20줄 기준의 비트마스크를 함께 돌려준다(애니메이션용).
//
// 아래에서 위로 훑으면서 지운 뒤 **같은 y 를 다시 검사한다** —
// 끌어내린 줄이 또 꽉 차 있을 수 있기 때문이다. 이 한 줄을 빠뜨리면
// 테트리스(4줄)가 2줄만 지워진다.
func (b *Board) ClearLines() (int, uint32) {
	n := 0
	var mask uint32
	for y := H - 1; y >= 0; y-- {
		full := true
		for x := 0; x < W; x++ {
			if b[y*W+x] == 0 {
				full = false
				break
			}
		}
		if !full {
			continue
		}
		n++
		if y >= Hidden {
			mask |= 1 << uint(y-Hidden)
		}
		for yy := y; yy > 0; yy-- {
			copy(b[yy*W:(yy+1)*W], b[(yy-1)*W:yy*W])
		}
		clear(b[0:W])
		y++ // 같은 y 를 다시 검사한다
	}
	return n, mask
}

// PushRows 는 바닥에서 n 줄을 밀어 올린다. hole 은 뚫려 있는 칸의 x.
//
// 한 번에 올라오는 n 줄은 같은 구멍을 공유한다("클린 가비지").
// 구멍이 매 줄 달라지면 사실상 복구가 불가능해서 대전이 성립하지 않는다.
// 천장 밖으로 밀려난 줄은 그냥 사라진다 — 배열이 곧 필드 전체이므로.
//
// hole 이 판 밖이면 호출자가 골라 줘야 한다(Game.PushGarbage 가 RNG 로 고른다).
func (b *Board) PushRows(n, hole int) {
	if n <= 0 {
		return
	}
	if n > H {
		n = H
	}
	if hole < 0 || hole >= W {
		hole = 0
	}
	for y := 0; y < H-n; y++ {
		copy(b[y*W:(y+1)*W], b[(y+n)*W:(y+n+1)*W])
	}
	for y := H - n; y < H; y++ {
		row := b[y*W : (y+1)*W]
		for x := range row {
			row[x] = Garbage
		}
		row[hole] = 0
	}
}

// Empty 는 판이 완전히 비었는지 본다 (퍼펙트 클리어 판정).
func (b *Board) Empty() bool {
	for _, v := range b {
		if v != 0 {
			return false
		}
	}
	return true
}

// Paint 는 문자열 그림으로 판을 덮어쓴다. 테스트와 골든 트레이스 전용이다.
// 한 줄이 W 글자, '.' 은 빈칸, '#' 은 가비지, 그 외는 채운 칸.
// 그림의 마지막 줄이 필드의 바닥줄에 놓인다.
//
// 항상 판 전체를 먼저 지운다 — 트레이스의 라운드 사이에 이전 판이 남으면
// 두 구현이 그 자리에서 갈라진다.
func (b *Board) Paint(rows []string) {
	clear(b[:])
	for i, row := range rows {
		y := H - len(rows) + i
		if y < 0 || y >= H {
			continue
		}
		for x := 0; x < W && x < len(row); x++ {
			switch row[x] {
			case '.':
			case '#':
				b[y*W+x] = Garbage
			default:
				b[y*W+x] = 1
			}
		}
	}
}

// Rows 는 보이는 20줄을 사람이 읽을 수 있는 문자열로 만든다.
// 디버깅과 테스트 실패 메시지용 — 판이 어떻게 생겼는지 눈으로 봐야 할 때가 온다.
func (b *Board) Rows() []string {
	out := make([]string, 0, Vis)
	buf := make([]byte, W)
	for y := Hidden; y < H; y++ {
		for x := 0; x < W; x++ {
			switch v := b[y*W+x]; {
			case v == 0:
				buf[x] = '.'
			case v == Garbage:
				buf[x] = '#'
			default:
				buf[x] = PieceNames[v-1][0]
			}
		}
		out = append(out, string(buf))
	}
	return out
}

// FNV-1a 32비트의 상수. JS 쪽 도구와 같은 값을 써야 골든 트레이스를 대조할 수 있다.
const (
	fnvOffset = 2166136261
	fnvPrime  = 16777619
)

// BoardHash 는 판 전체의 FNV-1a 32비트 해시.
//
// 왜 해시인가. 골든 트레이스는 1500스텝 × 6시드의 판을 저장해야 하는데,
// 판을 통째로 저장하면 파일이 20 MB 를 넘는다. 해시 하나면 4바이트다.
// 충돌 확률은 무시할 수 있고, 어긋난 지점을 알려 주는 데는 그걸로 충분하다.
// (어디가 왜 다른지는 100스텝마다 저장하는 stats 스냅샷이 알려 준다)
func BoardHash(b *Board) uint32 {
	h := uint32(fnvOffset)
	for _, v := range b {
		h ^= uint32(v)
		h *= fnvPrime
	}
	return h
}
