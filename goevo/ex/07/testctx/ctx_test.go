// 슬라이드 p7-v124-testctx — T.Context 와 T.Chdir, Go 1.24
package ctx

import (
	"os"
	"path/filepath"
	"testing"
)

func TestContext(t *testing.T) {
	ctx := t.Context()
	t.Cleanup(func() {
		// Canceled after the test body, before cleanups run.
		t.Log("in cleanup, ctx.Err() =", ctx.Err())
	})
	t.Log("in test, ctx.Err() =", ctx.Err())
}

func TestChdir(t *testing.T) {
	dir := t.TempDir()
	t.Chdir(dir) // restored when the test ends
	wd, _ := os.Getwd()
	t.Log("same dir:", filepath.Base(wd) == filepath.Base(dir))
}
