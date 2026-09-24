// 슬라이드 p4-v19-aliasrepair — 옮겨 간 새 자리
package newpkg

// Config moved here from oldpkg.
type Config struct{ Name string }

// Describe accepts the type under its new name.
func Describe(c Config) string { return "config " + c.Name }
