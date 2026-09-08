"""덱에 실을 시연을 재현한다. 매번 같은 결과가 나오게 작업 파일을 되돌린다.

    python demo/run.py            # 전체
    python demo/run.py fix        # 버그 고치기 한 판만

대본 모델을 쓰므로 네트워크도 API 키도 필요 없다 — 그런데도
"모델 -> 도구 -> 결과 -> 모델" 루프는 실물 그대로 돈다.
"""
import os
import subprocess
import sys
from pathlib import Path

# 파이프나 파일로 받으면 한국어 Windows 는 cp949 라 ⚙·▶ 가 든 줄이 통째로 사라진다
# (console_sink 의 UnicodeEncodeError 를 버스가 삼킨다). 부모·자식 모두 UTF-8 로 고정한다.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
ENV = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}

HERE = Path(__file__).resolve().parent
WORK = HERE / "work"
CFG = HERE / ".mini_puppy"
BUGGY = "def add(a, b):\n    return a - b\n\n\ndef mul(a, b):\n    return a * b\n"
LINE = "─" * 62


def reset():
    WORK.mkdir(exist_ok=True)
    (WORK / "calc.py").write_text(BUGGY, encoding="utf-8")


def run(title, *argv):
    sys.stdout.write("\n%s\n[%s]  mini-puppy %s\n%s\n"
                     % (LINE, title, " ".join(argv), LINE))
    sys.stdout.flush()
    subprocess.run([sys.executable, "-m", "mini_puppy",
                    "--config-dir", str(CFG), "-C", str(WORK), "--quiet"]
                   + list(argv), cwd=str(HERE.parent), check=False, env=ENV)
    sys.stdout.flush()


SCENES = {
    "fix": lambda: run("버그를 찾아 고치고 확인까지",
                       "-p", "calc.add 가 이상하다. 고쳐줘"),
    "guard": lambda: run("도구 목록이 가드레일이다",
                         "--agent", "python-tutor", "--model", "허용목록-시험",
                         "-p", "mul 이름을 바꿔줘"),
}

if __name__ == "__main__":
    for name in (sys.argv[1:] or list(SCENES)):
        reset()
        SCENES[name]()
