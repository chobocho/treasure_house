---
description: 변경분을 저장소 컨벤션대로 커밋하고 origin main 에 푸시한다
argument-hint: [커밋 제목 힌트]
---
treasure_house 저장소의 현재 변경분을 커밋하고 푸시한다. 제목 힌트: $ARGUMENTS

1. `git status --short` 와 `git diff --stat` 으로 변경분을 확인한다. scratch/·node_modules·빌드 캐시 같은 산출물은 빼고, 서로 무관한 변경이 섞였으면 커밋을 나눈다.
2. 덱 HTML 이 바뀌었으면 `tools/embed_mono_font.py` 의 `--check` 로 글꼴 내장을 검사한다. 장수·항목 수가 바뀌었으면 `index.html` 카드와 `README.md` 가 같은 커밋에 들어가는지 확인한다.
3. 빌드형 덱(…/deck/sections 경유)은 해당 프로젝트의 `make all` 이 초록일 때만 커밋한다. 검증하지 않았으면 커밋하지 말고 보고한다.
4. `history.md` 맨 위에 이번 작업 항목이 없으면 전역 CLAUDE.md §3 형식으로 덧붙인다(30항목을 넘으면 §3.2 순환을 먼저 별도 커밋).
5. 커밋 메시지는 접두사 없는 한국어 서술형. 리뷰 커밋은 결함을 종류별로 세어 제목에 남긴다. 끝에 Co-Authored-By 줄을 붙인다.
6. `git push origin main`. 거부되면 force 하지 말고 이유를 보고한다.
7. 커밋 해시와 푸시 결과를 한국어로 짧게 보고한다.
