"""mini-puppy — Code Puppy의 뼈대만 남긴 최소 코딩 에이전트.

표준 라이브러리만 쓴다. 외부 의존성 없음, 파이썬 3.11+.
각 모듈은 Code Puppy의 한 층에 대응한다:

    bus.py      <- code_puppy/messaging/bus.py
    config.py   <- code_puppy/config.py
    tools.py    <- code_puppy/tools/common.py
    fs_tools.py <- code_puppy/tools/file_operations.py, file_modifications.py
    sh_tools.py <- code_puppy/tools/command_runner.py
    history.py  <- code_puppy/agents/_history.py, _compaction.py
    model.py    <- code_puppy/model_factory.py, round_robin_model.py
    agent.py    <- code_puppy/agents/_runtime.py
    registry.py <- code_puppy/agents/agent_manager.py, json_agent.py
    session.py  <- code_puppy/session_storage.py, atomic_json.py
    cli.py      <- code_puppy/main.py, cli_runner.py
"""

__version__ = "0.1.0"
