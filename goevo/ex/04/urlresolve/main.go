// 슬라이드 p4-v110-url — ResolveReference 와 이중 빗금, Go 1.10
package main

import (
	"fmt"
	"net/url"
)

func main() {
	base, _ := url.Parse("http://host//path//to/page1")
	target, _ := url.Parse("page2")
	fmt.Println(base.ResolveReference(target))
}
