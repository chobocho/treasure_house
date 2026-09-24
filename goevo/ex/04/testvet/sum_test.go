// 슬라이드 p4-v110-testvet — go test 앞의 vet(일부러 틀림), Go 1.10
package testvet

import "testing"

func TestSum(t *testing.T) {
	if 2+2 != 4 {
		t.Errorf("sum is %d", "four") // wrong verb for a string
	}
}
