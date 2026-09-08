"""설정 — 세 겹으로 쌓고 위에서부터 읽는다.

    1. 환경변수  MINI_PUPPY_<KEY 대문자>     (CI·일회성 실행)
    2. 설정 파일 ~/.mini_puppy/puppy.cfg     (사람이 고치는 것)
    3. 기본값    DEFAULTS                    (코드에 박힌 것)

Code Puppy 의 config.py 도 같은 순서다. 규칙 하나만 지키면 된다:
**위층이 아래층을 가린다. 아래층은 절대 위층을 못 이긴다.**

파일은 mtime 으로 캐시한다 — REPL 이 매 턴 설정을 읽는데 매번 디스크를
때리면 느리고, 캐시만 하면 사용자가 파일을 고쳐도 반영이 안 된다.
"""

from __future__ import annotations

import configparser
import os
from pathlib import Path
from typing import Any

SECTION = "puppy"

DEFAULTS: dict[str, str] = {
    "model": "scripted",           # 기본 모델 이름 (models.json 의 키)
    "agent": "mini-puppy",         # 시작 에이전트
    "yolo_mode": "false",          # true 면 파일 수정에 확인을 묻지 않는다
    "compaction_threshold": "0.75",  # 창의 몇 %에서 컴팩션을 켜나
    "protected_tokens": "2000",    # 최근 대화 중 절대 안 지우는 분량
    "context_window": "16000",     # 모델 창 크기(토큰)
    "max_tool_output": "8000",     # 도구 결과 1건의 최대 글자 수
    "command_timeout": "30",       # 셸 명령 제한 시간(초)
    "max_subagent_depth": "3",     # 서브에이전트 재귀 한계
    "session_dir": "",             # 빈 값이면 <config_dir>/sessions
}

_TRUE = {"1", "true", "yes", "on", "y"}


class Config:
    def __init__(self, config_dir: str | os.PathLike | None = None,
                 environ: dict | None = None) -> None:
        self.dir = Path(config_dir) if config_dir else self.default_dir()
        self.path = self.dir / "puppy.cfg"
        self.environ = os.environ if environ is None else environ
        self._cache: dict[str, str] = {}
        self._cache_stamp: tuple[float, int] | None = None

    @staticmethod
    def default_dir() -> Path:
        return Path(os.path.expanduser("~")) / ".mini_puppy"

    # ---- 층 2: 파일 -------------------------------------------------
    def _stamp(self) -> tuple[float, int] | None:
        try:
            st = self.path.stat()
        except OSError:
            return None
        return (st.st_mtime, st.st_size)

    def _file_layer(self) -> dict[str, str]:
        stamp = self._stamp()
        if stamp is not None and stamp == self._cache_stamp:
            return self._cache          # 캐시 적중
        parser = configparser.ConfigParser()
        try:
            parser.read(self.path, encoding="utf-8")
        except (OSError, configparser.Error):
            self._cache, self._cache_stamp = {}, stamp
            return {}
        got = dict(parser[SECTION]) if parser.has_section(SECTION) else {}
        self._cache, self._cache_stamp = got, stamp
        return got

    # ---- 층 1: 환경변수 ---------------------------------------------
    def _env_key(self, key: str) -> str:
        return "MINI_PUPPY_" + key.upper()

    # ---- 읽기 --------------------------------------------------------
    def get(self, key: str, default: Any = None) -> Any:
        env = self.environ.get(self._env_key(key))
        if env is not None:
            return env
        got = self._file_layer().get(key)
        if got is not None:
            return got
        if key in DEFAULTS:
            return DEFAULTS[key]
        return default

    def source(self, key: str) -> str:
        """이 값이 어느 층에서 왔는지. /diag 가 이걸 보여 준다."""
        if self.environ.get(self._env_key(key)) is not None:
            return "env"
        if self._file_layer().get(key) is not None:
            return "file"
        if key in DEFAULTS:
            return "default"
        return "none"

    def get_bool(self, key: str) -> bool:
        return str(self.get(key, "")).strip().lower() in _TRUE

    def get_int(self, key: str) -> int:
        return int(float(self.get(key, 0)))

    def get_float(self, key: str) -> float:
        return float(self.get(key, 0.0))

    # ---- 쓰기 --------------------------------------------------------
    def set(self, key: str, value: Any) -> None:
        """파일 층에만 쓴다. 환경변수는 건드리지 않는다.

        환경변수가 덮고 있는 키를 set 해도 get 은 여전히 환경변수를 준다 —
        의도한 것이다. 껍데기가 아니라 진짜 우선순위를 보여 줘야 한다.
        """
        parser = configparser.ConfigParser()
        if self.path.exists():
            parser.read(self.path, encoding="utf-8")
        if not parser.has_section(SECTION):
            parser.add_section(SECTION)
        parser.set(SECTION, key, str(value))
        self.dir.mkdir(parents=True, exist_ok=True)
        from .session import atomic_write_text
        buf = []

        class _W:
            def write(self, s):  # configparser 는 파일 객체를 원한다
                buf.append(s)

        parser.write(_W())
        atomic_write_text(self.path, "".join(buf))
        self._cache_stamp = None        # 다음 읽기에서 다시 읽게

    def unset(self, key: str) -> None:
        parser = configparser.ConfigParser()
        if not self.path.exists():
            return
        parser.read(self.path, encoding="utf-8")
        if parser.has_section(SECTION) and parser.has_option(SECTION, key):
            parser.remove_option(SECTION, key)
            from .session import atomic_write_text
            buf = []

            class _W:
                def write(self, s):
                    buf.append(s)

            parser.write(_W())
            atomic_write_text(self.path, "".join(buf))
        self._cache_stamp = None

    def as_dict(self) -> dict[str, str]:
        out = dict(DEFAULTS)
        out.update(self._file_layer())
        for key in list(out) + [k for k in DEFAULTS]:
            env = self.environ.get(self._env_key(key))
            if env is not None:
                out[key] = env
        return out

    @property
    def sessions_dir(self) -> Path:
        raw = str(self.get("session_dir") or "").strip()
        return Path(raw) if raw else self.dir / "sessions"

    @property
    def agents_dir(self) -> Path:
        return self.dir / "agents"
