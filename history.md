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
