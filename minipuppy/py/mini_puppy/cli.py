"""명령줄 껍데기 — 두 가지 모드로 돈다.

    mini-puppy                      대화형 REPL
    mini-puppy -p "이 함수 고쳐"    한 번 돌고 끝(파이프·CI 용)

한 번 모드는 승인 창구가 없으므로 yolo 를 강제한다. 대신 --dry-run 을 주면
파일을 안 건드리고 무엇을 하려 했는지만 보여 준다.

슬래시 명령은 데코레이터로 등록한다 — 새 명령을 더하려면 함수 하나만 쓰면 된다.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from .agent import CancelToken
from .bus import MessageBus, console_sink
from .config import Config
from .factory import build_model, load_models
from .fs_tools import Workspace
from .history import History
from .registry import AgentRegistry, register_subagent_tool
from .session import Session, SessionStore
from .tools import ToolRegistry
from . import fs_tools, sh_tools

COMMANDS: dict = {}


def command(name: str, help_text: str):
    def wrap(fn):
        COMMANDS[name] = (fn, help_text)
        return fn
    return wrap


class Shell:
    def __init__(self, root: str, config: Config, bus: MessageBus) -> None:
        self.config = config
        self.bus = bus
        self.tools = ToolRegistry()
        fs_tools.register(self.tools)
        sh_tools.register(self.tools, default_timeout=config.get_int("command_timeout"))
        self.agents = AgentRegistry(config.agents_dir)
        register_subagent_tool(self.tools, self.agents, self._model_for,
                               bus=bus, config=config,
                               max_depth=config.get_int("max_subagent_depth"))
        self.models = load_models(config.dir / "models.json")
        self.model_name = config.get("model")
        self.agent_name = config.get("agent")
        self.ws = Workspace(root, yolo=config.get_bool("yolo_mode"),
                            approver=self.ask)
        self.ws.depth = 0
        self.store = SessionStore(config.sessions_dir)
        self.session = Session(agent=self.agent_name)
        self.history: History | None = None
        self.cancel = CancelToken()
        self.running = True

    # ---- 창구 ---------------------------------------------------------
    def ask(self, action: str, rel: str) -> bool:
        try:
            answer = input("  %s %s — 할까? [y/N] " % (action, rel))
        except (EOFError, KeyboardInterrupt):
            return False
        return answer.strip().lower() in ("y", "yes", "예")

    def _model_for(self, spec) -> object:
        return build_model(spec.model or self.model_name, self.models)

    def agent(self):
        model = build_model(self.model_name, self.models)
        agent = self.agents.build(self.agent_name, model, self.tools,
                                  bus=self.bus, config=self.config)
        if self.history is None:
            self.history = agent.new_history()
        return agent

    # ---- 한 턴 ---------------------------------------------------------
    def turn(self, text: str) -> None:
        if text.startswith("/"):
            self.slash(text)
            return
        if text.startswith("!"):
            self.slash("/sh " + text[1:])
            return
        agent = self.agent()
        self.cancel.reset()
        result, self.history = agent.run(text, self.history, ctx=self.ws,
                                         cancel=self.cancel)
        if result.stopped != "done":
            self.bus.warn("멈춘 이유: %s %s" % (result.stopped, result.error))
        self.session.messages = self.history.to_list()
        self.session.agent = self.agent_name
        if not self.session.title:
            self.session.title = text[:40]
        self.store.save(self.session)

    def slash(self, line: str) -> None:
        name, _, rest = line[1:].partition(" ")
        entry = COMMANDS.get(name)
        if entry is None:
            self.bus.warn("모르는 명령: /%s — /help 를 봐라" % name)
            return
        entry[0](self, rest.strip())


@command("help", "명령 목록")
def _help(sh: Shell, arg: str) -> None:
    rows = ["/%-10s %s" % (n, h) for n, (_f, h) in sorted(COMMANDS.items())]
    rows.append("!<명령>     셸 명령 바로 실행")
    sh.bus.info("\n".join(rows))


@command("agent", "에이전트 보기/바꾸기")
def _agent(sh: Shell, arg: str) -> None:
    if not arg:
        sh.bus.info("지금: %s\n%s" % (sh.agent_name, sh.agents.describe()))
        return
    if sh.agents.get(arg) is None:
        sh.bus.warn("모르는 에이전트: %s" % arg)
        return
    sh.agent_name = arg
    sh.history = None          # 인격이 바뀌면 시스템 프롬프트가 바뀐다 -> 새 기록
    sh.bus.info("에이전트를 %s 로 바꿨다. 대화 기록은 새로 시작한다." % arg)


@command("model", "모델 보기/바꾸기")
def _model(sh: Shell, arg: str) -> None:
    if not arg:
        sh.bus.info("지금: %s\n있는 것: %s"
                    % (sh.model_name, ", ".join(sorted(sh.models))))
        return
    if arg not in sh.models:
        sh.bus.warn("models.json 에 없다: %s" % arg)
        return
    sh.model_name = arg
    sh.bus.info("모델을 %s 로 바꿨다. 대화 기록은 그대로다." % arg)


@command("tools", "지금 에이전트가 쓸 수 있는 도구")
def _tools(sh: Shell, arg: str) -> None:
    spec = sh.agents.get(sh.agent_name)
    allow = spec.tools if spec else None
    rows = ["%-16s %s" % (t.name, t.description)
            for t in sh.tools.allowed(allow)]
    blocked = [n for n in sh.tools.names()
               if allow is not None and n not in set(allow)]
    out = "\n".join(rows)
    if blocked:
        out += "\n\n막힌 도구: " + ", ".join(blocked)
    sh.bus.info(out)


@command("compact", "지금 바로 기록을 접는다")
def _compact(sh: Shell, arg: str) -> None:
    if sh.history is None:
        sh.bus.info("접을 기록이 없다.")
        return
    before = sh.history.total_tokens()
    got = sh.history.compact(sh.config.get_int("protected_tokens"))
    if got is None:
        sh.bus.info("접을 중간 구간이 없다. (%d토큰)" % before)
    else:
        sh.bus.info("%d건을 접었다. %d -> %d토큰"
                    % (got[0], before, sh.history.total_tokens()))


@command("config", "설정 보기 / key=value 로 쓰기")
def _config(sh: Shell, arg: str) -> None:
    if "=" in arg:
        key, _, val = arg.partition("=")
        sh.config.set(key.strip(), val.strip())
        sh.bus.info("%s = %s (%s 층)"
                    % (key.strip(), sh.config.get(key.strip()),
                       sh.config.source(key.strip())))
        return
    rows = ["%-22s %-10s %s" % (k, sh.config.source(k), v)
            for k, v in sorted(sh.config.as_dict().items())]
    sh.bus.info("\n".join(rows))


@command("session", "세션 목록 / load <id> / new")
def _session(sh: Shell, arg: str) -> None:
    verb, _, rest = arg.partition(" ")
    if verb == "new" or not arg and False:
        sh.session = Session(agent=sh.agent_name)
        sh.history = None
        sh.bus.info("새 세션: %s" % sh.session.id)
        return
    if verb == "load":
        got = sh.store.load(rest.strip())
        if got is None:
            sh.bus.warn("없는 세션: %s" % rest.strip())
            return
        sh.session = got
        sh.history = History.from_list(got.messages)
        sh.agent_name = got.agent or sh.agent_name
        sh.bus.info("세션 %s 를 이어 연다 (메시지 %d건)"
                    % (got.id, len(got.messages)))
        return
    rows = ["%s  %-20s %s" % (s.id, (s.title or "(제목 없음)")[:20],
                              "%d건" % len(s.messages))
            for s in sh.store.list()[:20]]
    sh.bus.info("\n".join(rows) if rows else "(저장된 세션 없음)")


@command("sh", "셸 명령 실행")
def _sh(sh: Shell, arg: str) -> None:
    if not arg:
        sh.bus.warn("실행할 명령을 줘라.")
        return
    out = sh.tools.call("run_command", {"command": arg}, ctx=sh.ws)
    sh.bus.emit("tool_out" if out.ok else "error", out.content)


@command("quit", "끝낸다")
def _quit(sh: Shell, arg: str) -> None:
    sh.running = False


BANNER = r"""
   ___  ___       _        ___
  |     |  |  ___  |         |
  |__   |__|  |    |  ___    |    mini-puppy — Code Puppy 를 뼈대만 남긴 것
  |     |  |  |    |  |  |   |    /help 로 명령 목록, /quit 로 끝
  |     |  |  |__  |  |__|   |
"""


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="mini-puppy",
                                description="아주 작은 코딩 에이전트")
    p.add_argument("-p", "--prompt", help="한 번만 돌리고 끝낸다")
    p.add_argument("-C", "--chdir", default=".", help="작업 뿌리")
    p.add_argument("--config-dir", default=None, help="설정 디렉터리")
    p.add_argument("--agent", default=None, help="시작 에이전트")
    p.add_argument("--model", default=None, help="시작 모델")
    p.add_argument("--yolo", action="store_true", help="쓰기 확인을 묻지 않는다")
    p.add_argument("--quiet", action="store_true", help="배너를 안 그린다")
    p.add_argument("--max-steps", type=int, default=20)
    return p


def make_shell(args) -> Shell:
    config = Config(args.config_dir)
    bus = MessageBus()
    bus.subscribe(console_sink)
    shell = Shell(os.path.abspath(args.chdir), config, bus)
    if args.agent:
        shell.agent_name = args.agent
    if args.model:
        shell.model_name = args.model
    if args.yolo:
        shell.ws.yolo = True
    return shell


def main(argv: list | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        shell = make_shell(args)
    except Exception as exc:
        print("시작 실패: %s" % exc, file=sys.stderr)
        return 2

    if args.prompt:                       # 한 번 모드
        shell.ws.yolo = True              # 물어볼 사람이 없다
        try:
            shell.turn(args.prompt)
        except Exception as exc:
            print("실패: %s" % exc, file=sys.stderr)
            return 1
        return 0

    if not args.quiet:
        print(BANNER)
        print("  뿌리: %s" % shell.ws.root)
        print("  에이전트: %s   모델: %s\n" % (shell.agent_name, shell.model_name))
    while shell.running:
        try:
            line = input("🐶 > ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line:
            continue
        try:
            shell.turn(line)
        except KeyboardInterrupt:
            shell.cancel.cancel()
            print("\n(중단)")
        except Exception as exc:
            shell.bus.error("%s: %s" % (type(exc).__name__, exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
