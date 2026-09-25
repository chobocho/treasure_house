// 슬라이드 p8-v126-reflectiter — reflect 의 반복자 메서드, Go 1.26
package main

import (
	"fmt"
	"reflect"
	"strings"
)

type Release struct {
	Version string `json:"version"`
	Year    int    `json:"year"`
	secret  bool
}

func (r Release) String() string { return "go" + r.Version }
func (r Release) Old() bool      { return r.Year < 2020 }

func main() {
	v := reflect.ValueOf(Release{"1.26", 2026, true})

	// Value.Fields yields (StructField, Value) pairs.
	for f, fv := range v.Fields() {
		if f.IsExported() {
			fmt.Printf("field %-7s %-6s tag=%q = %v\n",
				f.Name, f.Type, f.Tag.Get("json"), fv)
		}
	}
	// Value.Methods yields (Method, Value) pairs, callable.
	for m, mv := range v.Methods() {
		fmt.Println("method", m.Name, "->", mv.Call(nil)[0])
	}
	// Type.Ins and Type.Outs iterate over a function's signature.
	ft := reflect.TypeFor[func(string, int) (bool, error)]()
	var sig []string
	for t := range ft.Ins() {
		sig = append(sig, "in "+t.String())
	}
	for t := range ft.Outs() {
		sig = append(sig, "out "+t.String())
	}
	fmt.Println(strings.Join(sig, ", "))
}
