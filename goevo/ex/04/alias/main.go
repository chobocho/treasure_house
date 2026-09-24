// 슬라이드 p4-v19-alias — 타입 별칭, Go 1.9
package main

import "fmt"

type Celsius float64 // a defined type: new and distinct

type Temp = Celsius // an alias: a second name, same type

func (c Celsius) String() string {
	return fmt.Sprintf("%.1f°C", float64(c))
}

func main() {
	var t Temp = 21.5
	var c Celsius = t // no conversion: it is the same type
	fmt.Println(t, c)
	fmt.Printf("%T %T\n", t, c)
}
