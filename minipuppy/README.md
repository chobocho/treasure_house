# minipuppy — Code Puppy 를 뼈대만 남겨 다시 만든 것

『월마트 AX와 Code Puppy』 덱 6·7부의 실물. 월마트가 공개한 코딩 에이전트
[code_puppy](https://github.com/mpfaffenberger/code_puppy)(파이썬 8만 7천 줄)에서
**구조를 결정하는 층만** 남겨 두 언어로 다시 썼다.

| | 위치 | 언어 | 의존성 | 시험 |
|---|---|---|---|---|
| mini-puppy | `py/` | Python 3.11+ | 표준 라이브러리만 | 96건 |
| minipuppy | `go/` | Go 1.21+ | 표준 라이브러리만 | (7부) |

## 왜 다시 만드는가

전략 문서는 추상적이고, 8만 7천 줄은 한 번에 안 읽힌다. 같은 구조를
1,700줄로 줄여 놓으면 **어느 결정이 본질이고 어느 것이 편의였는지** 보인다.

## 대응표

| mini-puppy | code_puppy | 무엇을 하는가 |
|---|---|---|
| `bus.py` | `messaging/bus.py` | 에이전트가 터미널을 직접 못 만지게 |
| `config.py` | `config.py` | 환경변수 > 파일 > 기본값 세 겹 |
| `tools.py` | `tools/common.py` | 서명→스키마, 허용 목록, 인자 형 맞춤 |
| `fs_tools.py` | `tools/file_*.py` | 읽기·쓰기·고치기·찾기 |
| `sh_tools.py` | `tools/command_runner.py` | 시간 제한·프로세스 나무 종료 |
| `history.py` | `agents/_history.py`, `_compaction.py` | 창이 넘치기 전에 접기 |
| `model.py` | `model_factory.py`, `round_robin_model.py` | 대본·HTTP·라운드로빈 |
| `factory.py` | `model_factory.py` | `models.json` → 모델 객체 |
| `agent.py` | `agents/_runtime.py` | 실행 루프 |
| `registry.py` | `agents/agent_manager.py`, `json_agent.py` | 인격 등록·서브에이전트 |
| `session.py` | `session_storage.py`, `atomic_io.py` | 원자적 저장·형식 이주 |
| `cli.py` | `main.py`, `cli_runner.py` | REPL·슬래시 명령·한 번 모드 |

## 돌려 보기

```bash
cd py
python -m unittest discover -s . -p "test_*.py"   # 96건
python demo/run.py                                 # 네트워크 없이 전체 루프 시연
python -m mini_puppy                               # 대화형 REPL
```

실제 모델을 붙이려면 `~/.mini_puppy/models.json` 에:

```json
{
  "gpt-4.1": {"type": "openai", "url": "https://api.openai.com/v1",
              "model_id": "gpt-4.1", "api_key": "$OPENAI_API_KEY"},
  "교대":    {"type": "round_robin", "models": ["gpt-4.1", "느린것"],
              "rotate_every": 4}
}
```

## 원본과 일부러 다르게 한 곳

| 항목 | code_puppy | mini-puppy | 왜 |
|---|---|---|---|
| 작업 뿌리 밖 접근 | 막지 않는다 | 막는다 | 교재에서 가드레일을 보여 주려고 |
| 라운드로빈 실패 처리 | 그대로 예외를 올린다 | 쿨다운을 걸고 건너뛴다 | 교대의 값어치가 드러나게 |
| 위험 명령 | 목록이 없다(확인으로만 막는다) | 짧은 거부 목록 | 확인 창구 없는 한 번 모드가 있으니 |
| 컴팩션 | 외부 라이브러리에 위임 | 직접 구현 | 이게 교재의 핵심이라 |
| 도구 결과 초과 | 10k 넘으면 파일로 흘린다 | 가운데를 자른다 | 더 단순한 쪽부터 |
