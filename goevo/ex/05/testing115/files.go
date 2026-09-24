// 슬라이드 p5-v115-testing — 시험할 함수, Go 1.15
package testing115

import (
	"os"
	"path/filepath"
)

// Save writes data to name inside dir.
func Save(dir, name, data string) error {
	return os.WriteFile(filepath.Join(dir, name), []byte(data), 0o644)
}
