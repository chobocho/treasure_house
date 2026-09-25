// 슬라이드 p10-ladder-1 — 타입 별칭, Go 1.9
package main

import "fmt"

type Celsius = float64

func main() { fmt.Println(Celsius(36.5)) }
