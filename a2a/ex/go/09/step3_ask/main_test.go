package main

import (
	"testing"

	"example.com/workshop/09/lodgingsuite"
)

// region: naive
// 같은 패키지(main)라 실행기 이름을 그대로 쓴다.
func TestStep3(t *testing.T) { lodgingsuite.Run(t, step3{}) }

// endregion
