// 슬라이드 p8-v125-testattr — T.Attr 와 T.Output, Go 1.25
package attr

import (
	"fmt"
	"testing"
)

func TestUpload(t *testing.T) {
	// A key/value pair that tools reading the log can pick up.
	t.Attr("ticket", "GO-1234")

	// Output is an io.Writer into the test log: indented like
	// t.Log, but without the file:line prefix.
	w := t.Output()
	fmt.Fprintln(w, "uploading 3 files")
	t.Log("done")
}
