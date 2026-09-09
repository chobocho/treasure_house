"""파일 도구 — 에이전트가 코드를 읽고 고치는 손.

가드레일이 두 겹이다.
  1. **작업 뿌리 밖으로 못 나간다.** 모델이 "../../.ssh/id_rsa" 를 달라고
     해도 경로를 정규화해 뿌리 밖이면 거절한다. 심볼릭 링크까지 풀어서 본다.
  2. **쓰기는 확인을 받는다.** yolo_mode 가 아니면 승인 콜백을 거친다.
     Ctrl-Z 가 없는 세계에서 되돌릴 수 없는 것은 먼저 물어야 한다.

edit_file 은 일부러 '찾아 바꾸기' 한 가지만 지원한다. 전체 덮어쓰기는
모델이 파일 뒷부분을 통째로 날려 먹는 사고가 잦고, 통합 diff 는 모델이
행 번호를 자주 틀린다. 유일한 문자열을 찾아 바꾸는 방식이 가장 안전하다.
"""

from __future__ import annotations

import fnmatch
import os
from pathlib import Path

from .tools import ToolError

SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv",
             ".mypy_cache", ".pytest_cache", "dist", "build", ".idea"}
MAX_READ_BYTES = 400_000


class Workspace:
    """뿌리 하나와 승인 정책을 들고 다니는 실행 문맥(ctx)."""

    def __init__(self, root: str | os.PathLike, yolo: bool = False,
                 approver=None) -> None:
        self.root = Path(root).resolve()
        self.yolo = yolo
        self.approver = approver          # (동작, 경로) -> bool
        self.writes: list[str] = []       # 이번 실행에서 건드린 파일

    def resolve(self, rel: str) -> Path:
        """뿌리 안쪽 경로만 돌려준다. 밖이면 ToolError."""
        if not rel or not str(rel).strip():
            raise ToolError("경로가 비었다.")
        candidate = (self.root / rel).expanduser()
        try:
            real = candidate.resolve()
        except OSError as exc:
            raise ToolError("경로를 풀 수 없다: %s" % exc)
        if real != self.root and self.root not in real.parents:
            raise ToolError("작업 뿌리 밖은 만질 수 없다: %s" % rel)
        return real

    def approve(self, action: str, path: Path) -> None:
        if self.yolo:
            return
        rel = os.path.relpath(path, self.root)
        if self.approver is None:
            raise ToolError("쓰기 승인이 필요한데 승인 창구가 없다: %s" % rel)
        if not self.approver(action, rel):
            raise ToolError("사용자가 거절했다: %s %s" % (action, rel))


def register(reg, ):
    """레지스트리에 파일 도구를 등록한다."""

    @reg.register
    def list_files(ctx: Workspace, path: str = ".", pattern: str = "*",
                   max_results: int = 200) -> str:
        """디렉터리를 재귀로 훑어 파일 목록을 준다.

        Args:
          path: 뿌리 기준 상대 경로
          pattern: 파일 이름 glob (예: *.py)
          max_results: 최대 몇 개까지
        """
        base = ctx.resolve(path)
        if not base.exists():
            raise ToolError("없는 경로: %s" % path)
        if base.is_file():
            return os.path.relpath(base, ctx.root).replace("\\", "/")
        out = []
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [d for d in sorted(dirnames) if d not in SKIP_DIRS]
            for name in sorted(filenames):
                if not fnmatch.fnmatch(name, pattern):
                    continue
                full = Path(dirpath) / name
                rel = os.path.relpath(full, ctx.root).replace("\\", "/")
                try:
                    size = full.stat().st_size
                except OSError:
                    size = 0
                out.append("%8d  %s" % (size, rel))
                if len(out) >= max_results:
                    out.append("… (%d개에서 끊음)" % max_results)
                    return "\n".join(out)
        return "\n".join(out) if out else "(없음)"

    @reg.register
    def read_file(ctx: Workspace, path: str, start: int = 1,
                  end: int = 0) -> str:
        """파일을 행 번호를 붙여 읽는다.

        Args:
          path: 뿌리 기준 상대 경로
          start: 시작 행 (1부터)
          end: 끝 행 (0 이면 끝까지)
        """
        target = ctx.resolve(path)
        if not target.is_file():
            raise ToolError("파일이 아니다: %s" % path)
        if target.stat().st_size > MAX_READ_BYTES:
            raise ToolError("너무 크다(%d바이트). start/end 로 잘라 읽어라."
                            % target.stat().st_size)
        try:
            lines = target.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            raise ToolError("텍스트 파일이 아니다: %s" % path)
        lo = max(1, start)
        hi = len(lines) if end <= 0 else min(len(lines), end)
        width = len(str(hi))
        body = [("%*d  %s" % (width, i, lines[i - 1])) for i in range(lo, hi + 1)]
        return "\n".join(body) if body else "(빈 파일)"

    @reg.register
    def write_file(ctx: Workspace, path: str, content: str) -> str:
        """파일을 새로 쓴다(있으면 통째로 덮는다).

        Args:
          path: 뿌리 기준 상대 경로
          content: 파일 전체 내용
        """
        target = ctx.resolve(path)
        ctx.approve("덮어쓰기" if target.exists() else "새로 만들기", target)
        from .session import atomic_write_text
        atomic_write_text(target, content)
        ctx.writes.append(os.path.relpath(target, ctx.root))
        return "%s 에 %d자 썼다." % (path, len(content))

    @reg.register
    def edit_file(ctx: Workspace, path: str, find: str, replace: str,
                  count: int = 1) -> str:
        """파일에서 찾은 문자열을 바꾼다. 유일하지 않으면 거절한다.

        Args:
          path: 뿌리 기준 상대 경로
          find: 찾을 문자열 (그대로, 정규식 아님)
          replace: 바꿀 문자열
          count: 몇 군데까지 바꿀지. 0 이면 전부
        """
        target = ctx.resolve(path)
        if not target.is_file():
            raise ToolError("파일이 아니다: %s" % path)
        text = target.read_text(encoding="utf-8")
        hits = text.count(find)
        if hits == 0:
            raise ToolError("찾는 문자열이 없다. 공백·들여쓰기까지 그대로 줘야 한다.")
        if count == 1 and hits > 1:
            raise ToolError("%d군데에서 걸린다. 앞뒤를 더 붙여 유일하게 만들거나 "
                            "count 를 지정해라." % hits)
        ctx.approve("고치기", target)
        new = text.replace(find, replace, hits if count == 0 else count)
        from .session import atomic_write_text
        atomic_write_text(target, new)
        ctx.writes.append(os.path.relpath(target, ctx.root))
        return "%s 에서 %d군데 바꿨다." % (path, hits if count == 0 else count)

    @reg.register
    def grep(ctx: Workspace, needle: str, pattern: str = "*",
             max_results: int = 100) -> str:
        """작업 뿌리 아래에서 문자열이 든 줄을 찾는다.

        Args:
          needle: 찾을 문자열
          pattern: 파일 이름 glob
          max_results: 최대 몇 줄까지
        """
        out = []
        for dirpath, dirnames, filenames in os.walk(ctx.root):
            dirnames[:] = [d for d in sorted(dirnames) if d not in SKIP_DIRS]
            for name in sorted(filenames):
                if not fnmatch.fnmatch(name, pattern):
                    continue
                full = Path(dirpath) / name
                try:
                    if full.stat().st_size > MAX_READ_BYTES:
                        continue
                    text = full.read_text(encoding="utf-8")
                except (OSError, UnicodeDecodeError):
                    continue
                rel = os.path.relpath(full, ctx.root).replace("\\", "/")
                for i, line in enumerate(text.splitlines(), 1):
                    if needle in line:
                        out.append("%s:%d: %s" % (rel, i, line.strip()[:200]))
                        if len(out) >= max_results:
                            return "\n".join(out)
        return "\n".join(out) if out else "(없음)"

    return reg
