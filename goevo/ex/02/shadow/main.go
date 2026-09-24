// 슬라이드 p2-v10-shadow — 가려진 결과 변수와 맨 return, Go 1
package main

func Bug() (i, j, k int) {
	for i = 0; i < 5; i++ {
		for j := 0; j < 5; j++ { // Redeclares j.
			k += i * j
			if k > 100 {
				return // Rejected: j is shadowed here.
			}
		}
	}
	return // OK: j is not shadowed here.
}

func main() { Bug() }
