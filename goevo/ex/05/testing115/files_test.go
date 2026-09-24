// 슬라이드 p5-v115-testing — T.TempDir·os.Exit 없는 TestMain, Go 1.15
package testing115

import (
	"fmt"
	"os"
	"path/filepath"
	"testing"
)

func TestSave(t *testing.T) {
	dir := t.TempDir() // removed after the test
	if err := Save(dir, "a.txt", "hi"); err != nil {
		t.Fatal(err)
	}
	b, _ := os.ReadFile(filepath.Join(dir, "a.txt"))
	t.Logf("read back %q", b)
}

func TestMain(m *testing.M) {
	fmt.Println("setup")
	m.Run() // Go 1.15: returning is enough, no os.Exit(m.Run())
}
