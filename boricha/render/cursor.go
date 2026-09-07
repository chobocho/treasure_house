package render

import "strings"

// trimForClear 는 줄 끝의 공백을 떼어 낸다 — 뗄 수 있을 때만.
//
// 우리는 줄을 쓰기 직전에 \e[K 로 커서부터 줄 끝까지를 지운다. 그러니 그 뒤에 이어지는
// 공백은 이미 지워진 자리를 다시 공백으로 덮는 셈이라 보낼 필요가 없다.
// 폭 80칸을 가득 채운 스타일 상자는 대개 절반이 공백이다 — 여기서 프레임이 반으로 준다.
//
// 딱 하나 뗄 수 없는 경우가 있다. 배경색이 걸린 줄이다.
// "\e[44m  텍스트    \e[0m" 에서 뒤의 공백은 "파란 칸" 이라는 그림의 일부다.
// \e[K 는 **지금 설정된 배경색으로** 지우기 때문에 그 자리가 파랗게 되리라 기대할 수 없다
// (줄 끝에서 이미 \e[0m 으로 되돌렸으므로 기본 배경으로 지워진다).
// 그래서 시퀀스가 하나라도 든 줄은 그대로 둔다. 안전한 쪽을 고른 것이다.
func trimForClear(line string) string {
	if strings.IndexByte(line, 0x1b) >= 0 {
		return line
	}
	return strings.TrimRight(line, " ")
}
