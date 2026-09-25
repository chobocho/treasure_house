// 슬라이드 p8-v126-artifact — T.ArtifactDir, Go 1.26
package report

import (
	"fmt"
	"os"
	"path/filepath"
	"testing"
)

func TestReport(t *testing.T) {
	out := Render(3)
	dir := t.ArtifactDir() // kept only with go test -artifacts
	path := filepath.Join(dir, "report.txt")
	if err := os.WriteFile(path, []byte(out), 0o644); err != nil {
		t.Fatal(err)
	}

	// Show where it went, hiding the random last element.
	wd, _ := os.Getwd()
	rel, err := filepath.Rel(wd, filepath.Dir(dir))
	if err != nil || filepath.IsAbs(rel) || rel[0] == '.' {
		rel = "(a temporary directory)"
	}
	fmt.Println("artifact dir:", filepath.ToSlash(rel)+"/<random>")
}
