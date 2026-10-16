package workshop

import "path/filepath"

// FixturePath 는 fixtures/ 아래 파일(예: keys/jwks.json)의 경로다.
// 에이전트가 키 파일을 workshop.json 과 같은 방법으로 찾게 한다.
func FixturePath(rel string) string {
	dir, err := fixturesDir()
	if err != nil {
		panic(err)
	}
	return filepath.Join(dir, rel)
}
