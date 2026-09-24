// 슬라이드 p5-v114-cleanup — T.Cleanup 은 나중에 등록한 것부터, Go 1.14
package cleanup

import "testing"

// openStore is a helper: the caller never has to remember Close.
func openStore(t *testing.T, name string) *Store {
	t.Helper()
	s := Open(name)
	t.Cleanup(func() {
		s.Close()
		t.Log("closed", name)
	})
	return s
}

func TestTwoStores(t *testing.T) {
	a := openStore(t, "a")
	b := openStore(t, "b")
	t.Log("using", a.Name, b.Name)
}
