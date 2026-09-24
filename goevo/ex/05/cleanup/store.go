// 슬라이드 p5-v114-cleanup — 시험할 작은 저장소, Go 1.14
package cleanup

// Store is a toy resource that must be closed.
type Store struct {
	Name   string
	closed bool
}

// Open returns an open Store.
func Open(name string) *Store { return &Store{Name: name} }

// Close marks the store closed.
func (s *Store) Close() { s.closed = true }
