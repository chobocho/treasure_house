// 시험할 때만 agents/lodging 에 놓이는 파일 — 09/run_tests 가
// go test -overlay 로 그 디렉터리에 있는 것처럼 보이게 한다.
package main

import (
	"testing"

	"example.com/workshop/09/lodgingsuite"
)

// region: suite
// 같은 패키지(main)가 되므로 소문자 executor 도 보인다.
func TestLodging(t *testing.T) { lodgingsuite.Run(t, executor{}) }

// endregion
