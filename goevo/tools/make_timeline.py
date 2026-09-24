# 연표 초안 — 날짜는 문서에서 기계가, 사건 글만 사람이 적는다.
# 결과는 data/timeline.tsv 의 출발점이다(goevo/ 에서 python3 tools/make_timeline.py).
# 이 스크립트가 아니라 표 자체를 고친다(PLAN.md §1: timeline.tsv 는 HAND).
import io, re, datetime, html
BASE = '.'
def read(p):
    return io.open(p, encoding='utf-8').read()
MON = {m: i for i, m in enumerate(['January','February','March','April','May','June','July',
       'August','September','October','November','December'], 1)}
idx = read('docs/raw/blog/index.txt')
blog = {}
for m in re.finditer(r'<a href="/blog/([^"]+)">([^<]*)</a>, <span class="date">(\d+) (\w+) (\d{4})</span>', idx):
    blog[m.group(1)] = '%s-%02d-%02d' % (m.group(5), MON[m.group(4)], int(m.group(3)))
rows = []
def add(date, ev, src, how):
    rows.append((date, ev, src, how))
faq = 'https://go.dev/doc/faq'
add('2007-09-21', '그리저머·파이크·톰프슨이 화이트보드에 새 언어의 목표를 그리기 시작', faq, 'docs/faq.txt §What is the history of the project?')
add('2007-09-25', '롭 파이크가 "Go" 라는 이름을 제안', 'https://go.dev/blog/toward-go2', 'docs/blog/toward-go2.txt §Introduction')
add('2008-01', '켄 톰프슨의 실험용 컴파일러(C 코드 출력) 시작', faq, 'docs/faq.txt 같은 절')
add('2008-05', '이안 테일러가 GCC 프런트엔드를 따로 시작', faq, 'docs/faq.txt 같은 절')
add('2009-11-10', 'Go 공개 — 오픈소스 프로젝트가 됨', faq, 'docs/faq.txt 같은 절')
add('2009-12-09', '주간 스냅숏 기록의 첫 항목', 'https://go.dev/doc/devel/weekly', 'docs/weekly.txt 마지막 절 제목')
for r, y, mo, d in re.findall(r'^§\t(r\d+) \(released (\d{4})/(\d\d)/(\d\d)\)', read('docs/pre_go1.txt'), re.M):
    add('%s-%s-%s' % (y, mo, d), '이름 붙은 안정판 %s' % r, 'https://go.dev/doc/devel/pre_go1', 'docs/pre_go1.txt 절 제목')
for line in read('data/releases.tsv').split('\n'):
    c = line.split('\t')
    if len(c) == 4 and c[2] == 'major':
        v = 'Go 1' if c[0] == 'go1' else 'Go ' + re.sub(r'^go|\.0$', '', c[0])
        add(c[1], '%s 릴리스' % v, 'https://go.dev/doc/devel/release', 'data/releases.tsv(docs/release.txt)')
EV = {
 'playground-intro': 'Go 플레이그라운드 소개',
 'defer-panic-and-recover': '블로그: defer·panic·recover',
 'json': '블로그: JSON 과 Go',
 'laws-of-reflection': '블로그: 리플렉션의 법칙',
 'tour': 'Go 투어 — 브라우저에서 배우기',
 'pprof': '블로그: Go 프로그램 프로파일링',
 'gccgo-in-gcc-471': 'GCC 4.7.1 에 gccgo',
 'first-go-program': '블로그: 첫 Go 프로그램',
 'gopher': '블로그: Go 고퍼',
 'pipelines': '블로그: 파이프라인과 취소',
 'errors-are-values': '블로그: 오류는 값이다',
 'examples': '블로그: 시험 가능한 예제',
 'go-brand': 'Go 의 새 브랜드',
 'go.dev': 'go.dev — 개발자 허브 공개',
 'pkgsite': 'pkg.go.dev 오픈소스화',
 'godoc.org-redirect': 'godoc.org 를 pkg.go.dev 로 넘김',
 'vscode-go': 'VS Code Go 확장이 Go 프로젝트로',
 'supply-chain': '블로그: 공급망 공격을 막는 방식',
 'vuln': '블로그: 취약점 관리',
 'govulncheck': 'govulncheck 1.0',
 'rebuild': '블로그: 완전히 재현되는 툴체인',
 'wasi': '블로그: WASI 지원',
 'wasmexport': '블로그: 확장 가능한 Wasm 애플리케이션',
 'fips140': '블로그: FIPS 140-3 암호 모듈',
 'generic-interfaces': '블로그: 제네릭 인터페이스',
 'allocation-optimizations': '블로그: 스택에 할당하기',
 'pkgsite-api': 'pkg.go.dev API 공개',
 'hello-world': 'Go 블로그의 첫 소식 글(2010년 3월의 새 소식)',
 '1year': '공개 1년 — 기여자 130명 이상',
 'declaration-syntax': '블로그: 선언 문법이 C 와 다른 까닭',
 'stable-releases': '태그 체계 변경 — weekly 와 release 를 가름',
 'introducing-gofix': 'gofix 소개',
 'go1-preview': 'Go 1 예고',
 'go1': 'Go 1 발표 — 첫 바이너리 배포판',
 'gofmt': '블로그: go fmt your code',
 'race-detector': '경쟁 검출기 소개',
 'cover': '블로그: 시험 커버리지 도구(go test -cover)',
 'generate': '블로그: go generate',
 'context': '블로그: context 동시성 패턴',
 'go15gc': '블로그: 낮은 지연을 앞세운 1.5 의 GC',
 'subtests': '블로그: 하위 시험과 하위 벤치마크',
 'go1.7-binary-size': '블로그: 1.7 의 더 작은 바이너리',
 'toward-go2': 'Toward Go 2 — GopherCon 2017 발표',
 'versioning-proposal': '패키지 버전 관리 제안(vgo)',
 'ismmkeynote': '블로그: Go GC 의 여정(ISMM 기조연설)',
 'go2draft': 'Go 2 초안 설계 공개(오류 처리·제네릭)',
 'go2-here-we-come': 'Go 2 제안 선정 기준',
 'modules2019': '블로그: 2019년의 모듈',
 'using-go-modules': '블로그: 모듈 쓰기 연재 시작',
 'go2-next-steps': 'Go 2 를 향한 다음 걸음',
 'why-generics': '블로그: 왜 제네릭인가',
 'module-mirror-launch': '모듈 미러와 체크섬 데이터베이스 가동',
 'go1.13-errors': '블로그: 1.13 의 오류 감싸기',
 'v2-go-modules': '블로그: 모듈 v2 와 그 너머',
 'generics-next-step': '블로그: 제네릭의 다음 걸음',
 'ports': '블로그: ARM 과 그 너머(애플 실리콘 이식)',
 'generics-proposal': '제네릭 제안(타입 매개변수) 공개',
 'go116-module-changes': '블로그: 1.16 의 모듈 변화',
 'fuzz-beta': '퍼징 베타',
 'intro-generics': '블로그: 제네릭 소개',
 'get-familiar-with-workspaces': '블로그: 워크스페이스',
 'go119runtime': '블로그: 4년 뒤의 Go 런타임',
 'pgo-preview': 'PGO 미리 보기',
 'compat': '블로그: 호환성과 "깨는 Go 2 는 없다"',
 'toolchain': '블로그: 앞으로의 호환성과 툴체인 관리',
 'slog': '블로그: 구조화된 로그 slog',
 'loopvar-preview': '블로그: 1.22 의 for 루프 고치기',
 'range-functions': '블로그: 함수에 대한 range',
 'unique': '블로그: unique 패키지',
 'gotelemetry': '블로그: 1.23 의 텔레메트리',
 'swisstable': '블로그: Swiss 테이블 map',
 'synctest': '블로그: testing/synctest',
 'osroot': '블로그: 경로 탈출에 강한 파일 API',
 'cleanups-and-weak': '블로그: 정리 함수와 약한 포인터',
 'coretypes': '블로그: 핵심 타입(core types)과의 작별',
 'testing-b-loop': '블로그: testing.B.Loop',
 'error-syntax': '블로그: 오류 처리 문법 제안을 멈춤',
 'container-aware-gomaxprocs': '블로그: 컨테이너를 아는 GOMAXPROCS',
 'jsonv2-exp': '블로그: 실험적 JSON v2',
 'greenteagc': '블로그: Green Tea GC',
 '16years': '블로그: Go 의 열여섯 해',
 'gofix': '블로그: go fix 로 코드 현대화',
 'inliner': '블로그: //go:fix inline 과 소스 수준 인라이너',
 'generic-methods': '블로그: 제네릭 메서드',
 'goroutine-leak-profiles': '블로그: 고루틴 누수 프로파일',
 'size-specialized-allocations': '블로그: 크기별 메모리 할당',
}
for slug, ev in EV.items():
    add(blog[slug], ev, 'https://go.dev/blog/' + slug, 'docs/blog/index.txt 제목·날짜')
add('2027-02', 'Go 1.28 예정(초안 노트의 말)', 'https://tip.golang.org/doc/go1.28', 'docs/relnotes/go1.28-draft.txt 셋째 줄')
rows.sort(key=lambda r: r[0])
out = ['# 연표 — 한 행에 사건 하나. 날짜는 문서에서(scratch/make_timeline.py 로 처음 뽑음), 사건 글은 손으로.',
       'date\tevent\tsource\tverified-how'] + ['\t'.join(r) for r in rows]
io.open('data/timeline.tsv', 'w', encoding='utf-8', newline='\n').write('\n'.join(out) + '\n')
print(len(rows), 'rows')
