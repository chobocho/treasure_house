# a2a-sdk 는 무엇에 기대고, extra(선택 설치 묶음)마다 무엇을 더 까는가.
#   python 07/sdk_extras.py
# 패키지 메타데이터(Requires-Dist)를 읽고, 이 venv 에 깔렸는지 본다.
from collections import defaultdict
from importlib import metadata

from packaging.requirements import Requirement


# region: extras
def installed(name):
    try:
        metadata.version(name)
        return True
    except metadata.PackageNotFoundError:
        return False


dist = metadata.distribution("a2a-sdk")
print("a2a-sdk", dist.version)
core, extras = [], defaultdict(set)
for line in dist.requires:
    req = Requirement(line)
    marker = str(req.marker or "")
    if "extra ==" in marker:
        extra = marker.split('"')[1]
        if extra != "all":  # all 은 나머지를 다 더한 것
            extras[extra].add(req.name)
    elif "python_full_version" not in marker:
        core.append(req.name)

print("늘 까는 것:", " ".join(sorted(core)))
for extra in sorted(extras):
    names = sorted(extras[extra])
    have = "".join("O" if installed(n) else "." for n in names)
    print(f"  {extra:<12} {have:<4}", " ".join(names))
# endregion
