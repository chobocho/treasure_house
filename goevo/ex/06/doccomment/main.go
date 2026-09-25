// 슬라이드 p6-v119-docpkg — go/doc/comment 로 주석 다루기, Go 1.19
package main

import (
	"fmt"
	"go/doc/comment"
)

const doc = `Package tally counts things.

# Usage

Call [New], then [Counter.Add]:
  - one item at a time
  - or many at once

See [the spec] for details.

[the spec]: https://go.dev/ref/spec
`

func main() {
	p := comment.Parser{
		// Pretend every [Name] is a symbol of this package.
		LookupSym: func(recv, name string) bool { return true },
	}
	d := p.Parse(doc)
	var pr comment.Printer
	fmt.Printf("%s", pr.Markdown(d))
	fmt.Println("---- blocks:", len(d.Content), "links:", len(d.Links))
}
