# 설치된 세 SDK 에서 트레이스 낱말을 센다 — 낱말이 든 파일의 수.
#   python 17/otel_grep.py
import os
import subprocess
from pathlib import Path

import a2a

go_cache = subprocess.run(
    ["go", "env", "GOMODCACHE"],
    capture_output=True,
    text=True,
    check=True,
).stdout.strip()
# region: count
SDKS = {
    "py a2a-sdk": Path(a2a.__file__).parent,
    "ts @a2a-js/sdk": Path("../ts/node_modules/@a2a-js/sdk/dist"),
    "go a2a-go": Path(
        go_cache, "github.com/a2aproject/a2a-go/v2@v2.6.0"
    ),
}
WORDS = ("opentelemetry", "traceparent", "tracestate")
CODE = (".py", ".js", ".go")  # 소스만 — 문서·타입 선언은 뺀다


def count(root, word):
    n = 0
    for d, _, files in os.walk(root):
        for f in files:
            if f.endswith(CODE) and not f.endswith("_test.go"):
                text = Path(d, f).read_text(errors="replace").lower()
                n += word in text
    return n


print(f"{'SDK':<16}" + "".join(f"{w:>15}" for w in WORDS))
for name, root in SDKS.items():
    row = "".join(f"{count(root, w):>15}" for w in WORDS)
    print(f"{name:<16}{row}")
# endregion
