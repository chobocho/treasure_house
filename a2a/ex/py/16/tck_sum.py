# TCK 보고서(compatibility.json · junitreport.xml)를 한 화면으로.
# 요구사항마다의 판정을 수준(MUST·SHOULD·MAY)별로 세고, FAIL 인
# 요구사항은 실패한 시험의 바인딩과 오류 글(겹치면 한 번)을 적는다.
#   python 16/tck_sum.py REPORTS_DIR
import json
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

reports = Path(sys.argv[1])
compat = json.loads((reports / "compatibility.json").read_text())
junit = ET.parse(reports / "junitreport.xml").getroot()

# region: count
LEVELS = ("MUST", "SHOULD", "MAY")
STATES = ("PASS", "FAIL", "SKIPPED", "NOT TESTED")
reqs = compat["per_requirement"]
count = Counter((r["status"], r["level"]) for r in reqs.values())
print(f"요구사항 {len(reqs)}개 — 판정 × 수준")
print(f"{'':12}" + "".join(f"{lv:>7}" for lv in LEVELS))
for st in STATES:
    print(f"{st:12}" + "".join(f"{count[st, lv]:>7}" for lv in LEVELS))
# endregion

# region: tests
cases = junit.iter("testcase")
failed = defaultdict(set)  # "파일::클래스::이름" → 바인딩들
n = Counter()
for c in cases:
    kids = {k.tag for k in c}
    kind = "failure" if "failure" in kids else "skipped" in kids
    n[{"failure": "실패", True: "건너뜀", False: "통과"}[kind]] += 1
    if "failure" in kids:
        mod, cls = c.get("classname").rsplit(".", 1)
        base = re.sub(r"\[(\w+)\]$", "", c.get("name"))
        m = re.search(r"\[(\w+)\]$", c.get("name"))
        key = f"{mod.replace('.', '/')}.py::{cls}::{base}"
        failed[key].add(m.group(1) if m else "-")
print(
    f"시험 {sum(n.values())}개: 통과 {n['통과']} · 실패 {n['실패']}"
    f" · 건너뜀 {n['건너뜀']}"
)
# endregion


def short(text):
    """오류 글에서 스펙 링크와 '(could be: …)' 후보 목록을 뗀다."""
    return re.split(r" \((?:see|could be:) ", text)[0]


# region: skips
skips = Counter(
    short(k.get("message", ""))
    for c in junit.iter("testcase")
    for k in c
    if k.tag == "skipped"
)
print("건너뜀·xfail 의 사유 — 횟수")
for why, k in sorted(skips.items(), key=lambda x: (-x[1], x[0])):
    print(f"{k:>4}", why)
# endregion

# region: fails
print("FAIL — 요구사항 · 수준 · 실패한 시험의 바인딩, 그 아래 오류 글")
for rid, r in reqs.items():
    if r["status"] != "FAIL":
        continue
    where = set()
    for t in r["test_ids"]:
        where |= failed.get(re.sub(r"\[\w+\]$", "", t), set())
    print(rid, r["level"], ",".join(sorted(where)) or "-")
    for e in dict.fromkeys(short(e) for e in r["errors"]):
        print("  ·", e)
# endregion

# region: untested
# 시험 파일이 그 id 를 부르는지로 가른다(부르는데 판정이 없으면 앞
# 단계에서 건너뛴 것이다). TCK 의 뿌리 = REPORTS_DIR 의 부모.
tests = " ".join(
    t.read_text() for t in (reports.parent / "tests").rglob("*.py")
)
NONE, IDLE = "시험이 없다", "시험은 있으나 앞 단계에서 멈췄다"
groups = {NONE: defaultdict(list), IDLE: defaultdict(list)}
for rid, r in reqs.items():
    if r["status"] == "NOT TESTED":
        head, num = rid.rsplit("-", 1)
        groups[IDLE if f'"{rid}"' in tests else NONE][head].append(num)
for kind, g in groups.items():
    print(f"NOT TESTED — {kind}")
    for head in sorted(g):
        print(f"  {head:<16}", " ".join(g[head]))
# endregion
# @ norun
