# -*- coding: utf-8 -*-
"""anon.py — 네이티브 캡처에서 이 기기를 가리키는 값을 가짜로 바꾼다.

    text = anon.native(text)    # run_all.py 가 들여올 때 부른다

scrub.py 는 개인정보(SSID·IP·집 경로)를 자리표시로 바꾼다. 여기는
그 밖에 "바로 이 폰" 을 좁히는 값을 맡는다 — 모델 번호, 커널 빌드
해시·펌웨어 번호·빌드 시각, 앱 PID, 배터리 수치, 센서 칩 이름,
카메라 사양, 미러 주소, 갱신 대기 패키지. 공개 저장소에 올리기 전에
사용자가 정했다(2026-09-19).

자리표시(<…>)가 아니라 그럴듯한 가짜를 쓰는 까닭: 덱이 JSON 의 칸
이름과 모양을 설명하므로 값이 JSON 으로 읽혀야 한다. 대신 덱의
"이 기기" 슬라이드가 가짜라는 것을 밝힌다. 덱이 결론을 끌어내는
측정값(시간·포트·셔뱅 결과·종료 코드)과 이미 공개된 캡처에 있는
값(uid·SELinux 문맥)은 건드리지 않는다.

두 번 불러도 결과가 같다. 시간 O(글자 수), 공간 O(글자 수).
"""
import json
import re

MODEL = 'SM-F000N'
PID = '1234'
MIRROR = 'https://packages-cf.termux.dev/apt/termux-main'
UPDATABLE = 'vim/stable 9.9.9 aarch64 [upgradable from: 9.9.8]'
# 칸 이름은 그대로 두고 수치만 — 상태 글자(CHARGING 등)는 덱이 쓴다
BATTERY = {'temperature': 30.0, 'voltage': 4000, 'current': 250000,
           'current_average': 250000, 'percentage': 50, 'level': 50,
           'charge_counter': 2000000}

MODEL_RE = re.compile(r'\bSM-[A-Z]\d{3}[A-Z]\b')
# GKI 판(6.12.58-android16-6)까지는 남기고 그 뒤의 빌드 꼬리만
KREL_RE = re.compile(r'(-android\d+-\d+)-\S+')
KDATE_RE = re.compile(r'(SMP PREEMPT) .*? UTC \d{4}')
PID_RE = re.compile(r'(TERMUX_APP__PID=)\d+')
MIRROR_RE = re.compile(r'https://\S+/termux-main\b')
UPD_RE = re.compile(r'(Updatable packages:\n)(?:[^\n]*\[upgradable'
                    r'[^\n]*\n)+')
SEC_RE = re.compile(r'(== \d+\. [^\n]*(termux-battery-status|'
                    r'termux-sensor -l|termux-camera-info)[^\n]* ==\n)'
                    r'(.*?)(\n\(종료 -?\d+\))', re.S)


def _battery(d):
    return dict((k, BATTERY.get(k, v)) for k, v in d.items())


def _sensors(d):
    n = len(d.get('sensors', []))
    return dict(d, sensors=['sensor-%02d' % (i + 1) for i in range(n)])


def _camera(cams):
    out = []
    for c in cams:
        c = dict(c)
        if 'jpeg_output_sizes' in c:
            c['jpeg_output_sizes'] = [{'width': 4000, 'height': 3000}]
        if 'focal_lengths' in c:
            c['focal_lengths'] = [4.0] * len(c['focal_lengths'])
        if 'physical_size' in c:
            c['physical_size'] = {'width': 5.0, 'height': 4.0}
        out.append(c)
    return out


FIX = {'termux-battery-status': _battery, 'termux-sensor -l': _sensors,
       'termux-camera-info': _camera}


def _json_sec(m):
    try:
        data = json.loads(m.group(3))
    except ValueError:
        return m.group(0)               # 끊겨 본문이 빈 절
    body = json.dumps(FIX[m.group(2)](data), indent=2,
                      ensure_ascii=False)
    return m.group(1) + body + m.group(4)


def native(text):
    """가짜로 바꾼 글. 측정값·종료 코드는 그대로."""
    text = MODEL_RE.sub(MODEL, text)
    text = KREL_RE.sub(r'\1-g0000000-4k', text)
    text = KDATE_RE.sub(r'\1 Thu Jan  1 00:00:00 UTC 2026', text)
    text = PID_RE.sub(r'\g<1>' + PID, text)
    text = MIRROR_RE.sub(MIRROR, text)
    text = UPD_RE.sub(r'\g<1>' + UPDATABLE + '\n', text)
    return SEC_RE.sub(_json_sec, text)
