"""세션 저장 — 40단계짜리 작업이 32단계에서 끊겨도 이어서 하기 위한 층.

핵심은 하나: **반쯤 쓰다 만 파일을 남기지 않는다.**
노트북이 절전되거나 Ctrl-C 가 들어와도, 디스크 위의 세션 파일은
"이전 상태" 아니면 "새 상태"다. 중간은 없다.

방법은 고전적이다 — 같은 디렉터리에 임시 파일로 다 쓰고, fsync 로
디스크에 확실히 내려보낸 뒤, os.replace 로 갈아 끼운다. os.replace 는
같은 볼륨 안에서 원자적이다(POSIX rename(2), Windows MoveFileEx).
"""

from __future__ import annotations

import json
import os
import tempfile
import time
import uuid
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 2


def atomic_write_text(path: str | os.PathLike, text: str, encoding: str = "utf-8") -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=path.name + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding=encoding, newline="\n") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())          # 내용이 진짜 디스크에 닿게
        os.replace(tmp, path)              # 여기서부터 새 내용
        tmp = None
    finally:
        if tmp is not None and os.path.exists(tmp):
            os.unlink(tmp)                 # 실패했으면 쓰레기를 남기지 않는다
    _fsync_dir(path.parent)


def _fsync_dir(directory: Path) -> None:
    """디렉터리 엔트리까지 내려야 rename 이 살아남는다. Windows 엔 없다."""
    if os.name == "nt":
        return
    try:
        fd = os.open(str(directory), os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(fd)
    except OSError:
        pass
    finally:
        os.close(fd)


def atomic_write_json(path: str | os.PathLike, obj: Any) -> None:
    atomic_write_text(path, json.dumps(obj, ensure_ascii=False, indent=2) + "\n")


def read_json(path: str | os.PathLike, default: Any = None) -> Any:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError):
        return default


@dataclass
class Session:
    """한 번의 대화. 메시지는 history.Message 의 dict 표현으로 담는다."""

    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    agent: str = "mini-puppy"
    title: str = ""
    created: float = field(default_factory=time.time)
    updated: float = field(default_factory=time.time)
    messages: list[dict] = field(default_factory=list)
    version: int = SCHEMA_VERSION

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, raw: dict) -> "Session":
        raw = migrate(dict(raw))
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in raw.items() if k in known})


def migrate(raw: dict) -> dict:
    """옛 세션 파일을 지금 형식으로 끌어올린다.

    Code Puppy 가 session_migration.py 를 따로 둔 이유와 같다: 형식을 바꾸면
    사용자의 지난 세션이 전부 열리지 않는다. 버전을 적어 두고 한 단계씩 올린다.
    """
    version = int(raw.get("version", 1))
    if version < 2:
        # v1 은 messages 가 [str, ...] 였다. v2 는 {role, content, ...}.
        fixed = []
        for m in raw.get("messages", []):
            if isinstance(m, str):
                fixed.append({"role": "user", "content": m})
            elif isinstance(m, dict):
                fixed.append(m)
        raw["messages"] = fixed
        raw.setdefault("agent", "mini-puppy")
        version = 2
    raw["version"] = version
    return raw


class SessionStore:
    def __init__(self, directory: str | os.PathLike) -> None:
        self.dir = Path(directory)

    def path_for(self, session_id: str) -> Path:
        return self.dir / f"{session_id}.json"

    def save(self, session: Session) -> Path:
        session.updated = time.time()
        path = self.path_for(session.id)
        atomic_write_json(path, session.to_dict())
        return path

    def load(self, session_id: str) -> Session | None:
        raw = read_json(self.path_for(session_id))
        if not isinstance(raw, dict):
            return None
        return Session.from_dict(raw)

    def list(self) -> list[Session]:
        out = []
        if not self.dir.exists():
            return out
        for path in sorted(self.dir.glob("*.json")):
            raw = read_json(path)
            if isinstance(raw, dict):
                try:
                    out.append(Session.from_dict(raw))
                except TypeError:
                    continue           # 알아볼 수 없는 파일은 조용히 건너뛴다
        out.sort(key=lambda s: s.updated, reverse=True)
        return out

    def delete(self, session_id: str) -> bool:
        path = self.path_for(session_id)
        if path.exists():
            path.unlink()
            return True
        return False
