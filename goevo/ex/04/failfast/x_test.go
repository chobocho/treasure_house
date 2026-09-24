// 슬라이드 p4-v110-failfast — -failfast(일부러 실패), Go 1.10
package failfast

import "testing"

func TestA(t *testing.T) { t.Error("A is broken") }

func TestB(t *testing.T) { t.Error("B is broken too") }

func TestC(t *testing.T) {}
