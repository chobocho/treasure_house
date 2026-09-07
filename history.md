### [2026-09-07 02:05] 보리차 3단계 — width 글자 폭 표(한글 두 칸 문제)
- **기획:** 터미널은 글자를 칸으로 센다. 한글·한자·이모지는 두 칸. Go 표준 라이브러리에 답이 없어 유니코드 East_Asian_Width 표를 직접 실어 이분 탐색한다. 네트워크가 없어 자료는 python unicodedata(16.0.0)에서 뽑아 형식과 출처를 파일 머리에 명시.
- **TC:** RuneWidth 23종(한글·전각·이모지·결합문자·한글자모·제어), StringWidth ANSI 무시, Truncate 경계(반 칸 불가·꾸밈 보존·0/음수), Pad, Wrap 낱말·강제분할·줄바꿈 보존, 폭 2~20 전수로 "어느 줄도 폭 초과 없음" 불변식.
- **개발:** width/{widthdata.txt,table.go(생성),width.go,truncate.go}, tools/gen_width/main.go, Makefile gen-width
- **검증:** go test 전 패키지 통과, go vet 무경고, 생성기 두 번 돌려 md5 동일(결정론)
- **비고:** 모호(A) 부류는 1칸으로 결정 — 박스 문자가 여기 속해 2칸으로 보면 상자가 두 배가 된다.

### [2026-09-07 01:59] 보리차 2단계 — input 입력 파서(바이트 → 사건)
- **기획:** 터미널 입력은 바이트로만 온다. CSI/SS3 문법을 상태 기계로 옮겨 키·마우스·붙여넣기·포커스로 바꾸는 층. tea 가 input 을 쓰는 방향이라 순환을 피해 input 을 먼저 만듦(PLAN §8 순서 변경, 로그에 기록).
- **TC:** 바이트→사건 대응표 70여 건(한글·이모지·조합키·SGR 마우스·붙여넣기), 같은 입력을 **모든 바이트 경계에서 잘라** 결과 동일 검증, 한 바이트씩 흘려넣기, 반쪽 UTF-8 대기·깨진 UTF-8 폐기, ESC 단독→Flush, 붙여넣기 중 Flush 무시, Reader 시계 4종.
- **개발:** input/{keys,decoder,mouse,paste,reader}.go + 테스트 3개
- **검증:** go test 통과(input·term), go vet 무경고, 교차 컴파일 유지, 누적 2,302줄
- **비고:** android/arm64 는 -race 미지원 — 경합 검증은 설계와 타이밍 테스트로 대신함.

### [2026-09-07 01:47] 보리차 1단계 — 모듈·Makefile·term 드라이버·날것 터미널 예제
- **기획:** boricha/PLAN.md의 §8 커밋 1. Bubble Tea 같은 TUI 프레임워크를 표준 라이브러리만으로 바닥부터. 첫 층은 터미널 드라이버와 "프레임워크 없이 해 보기" 데모.
- **TC:** 시퀀스 바이트 대조 21종, CursorTo/Up/Down/ToCol 경계값(0·음수), Cleanup 역순·멱등·켠 것만 되돌리기, MakeRaw 비트 산술(가짜 Termios 전비트 1), 무관 필드 보존, winsize 0×0 거부, 비터미널 오류.
- **개발:** boricha/go.mod, Makefile, term/{seq,term,term_unix,term_windows,termios_unix,termios_linux,termios_darwin}.go, examples/00_raw/main.go 외 3개 파일
- **검증:** go test 통과(term ok), go vet 무경고, GOOS=darwin/windows 교차 컴파일 성공, tmux 80×24 실캡처 out/tmux_00_raw.txt(방향키 = 1B 5B 44)
- **비고:** macOS termios 경로는 컴파일만 확인, 실행 미검증. 덱 조립은 §8 커밋 10부터.

### [2026-09-07 10:06] template.html 고정폭 글꼴(DeckMono) 내장과 tools/embed_mono_font.py
- **기획:** template 계열 덱이 Consolas·SF Mono를 앞세워 한글·박스 문자가 다른 글꼴로 빠지며 아스키 표가 깨짐. Bubble Tea 덱에서 검증한 D2Coding 서브셋 내장을 공용 스크립트로 일반화.
- **TC:** 고정폭 요소 글자 수집·엔티티 복원, ASCII·박스 항상 포함, 반각 500/전각 1000 폭 계약과 위반 감지, 이모지 경고, 삽입·제자리 교체·두 번 돌려도 동일·저장 시각 미기록·CRLF 보존·style 없음, check 4종 (19건).
- **개발:** tools/embed_mono_font.py, tools/test_embed_mono_font.py, template.html(고정폭 목록 17곳 통일·글꼴 21KB·글꼴 슬라이드 1장·사용법·점검·함정표), CLAUDE.md
- **검증:** 19 passed, 0 failed · template.html --check 통과 · Go_Bubble_Tea 덱 --check 통과 · 태그 균형 확인
- **비고:** 기존 template 계열 문서 20개는 후속 작업으로 같은 스크립트를 일괄 적용 예정. Playwright를 못 쓰는 환경이라 브라우저 렌더링은 눈으로 확인하지 못함.
