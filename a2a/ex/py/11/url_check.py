# 파이썬 SDK 의 SSRF 검사 — validate_push_notification_url 이 어떤
# 웹훅 주소를 받고 어떤 주소를 거절하나. 연결은 하지 않는다(주소만
# 푼다).
# 이름은 /etc/hosts 에 있는 localhost 하나만 쓴다 — DNS 없이 돌게.
import asyncio
import logging

from a2a.utils.push_url_validator import validate_push_notification_url

URLS = [
    "http://127.0.0.1:11148/",  # 이 덱의 웹훅 — 루프백
    "http://localhost/hook",  # 이름이 루프백으로 풀린다
    "http://10.0.0.5/hook",  # 사설망
    "http://169.254.169.254/latest/meta-data/",  # 클라우드 메타데이터
    "http://[::ffff:127.0.0.1]/",  # IPv6 에 싼 IPv4 루프백
    "ftp://203.0.113.7/hook",  # http(s) 가 아니다
    "https://8.8.8.8/hook",  # 공인 주소
]


async def main():
    logging.disable(logging.WARNING)  # 거절마다 찍는 경고는 끈다
    for url in URLS:
        ok = await validate_push_notification_url(url)
        print("받음" if ok else "거절", url)


asyncio.run(main())
