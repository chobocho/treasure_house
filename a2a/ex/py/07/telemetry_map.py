# 원격 측정은 어디에 붙어 있고, 지금 무엇을 기록하나.
#   python 07/telemetry_map.py
import pathlib
import re

import a2a
from a2a.utils import telemetry
from opentelemetry import trace

# region: map
root = pathlib.Path(a2a.__file__).parent
marks = re.compile(
    r"^@(trace_class|trace_function)\((.*)\)$", re.MULTILINE
)
for f in sorted(root.rglob("*.py")):
    if f.name == "telemetry.py":
        continue
    for m in marks.finditer(f.read_text()):
        kind = m.group(2).replace("kind=SpanKind.", "") or "INTERNAL"
        print(f"  {f.relative_to(root)!s:52} {kind}")
print("opentelemetry 있음:", telemetry.otel_installed)
print("스위치:", telemetry.ENABLED_ENV_VAR, "→", telemetry.otel_enabled)
provider = trace.get_tracer_provider()
span = trace.get_tracer("시험").start_span("x")
print("공급자:", type(provider).__name__)
print("만든 span:", type(span).__name__, "기록함:", span.is_recording())
# endregion
