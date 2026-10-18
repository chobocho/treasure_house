# 교통 에이전트에 푸시 설정을 단 배차를 returnImmediately 로 맡기고,
# 중계기(relay.py)에서 끝 알림이 지나가기를 기다려 온 것을 찍는다.
# 마지막에 GetTask 로 작업이 어떻게 끝났는지도 본다. SDK 없이 urllib.
#   python 11/notify.py 에이전트 웹훅 중계기 토큰 [--auth 스킴:값]
import argparse
import json
import urllib.request

BUS = {"headcount": 30, "nights": 1, "depart": "강남역"}


def rpc(url, method, params):
    body = {"jsonrpc": "2.0", "id": 1, "method": method}
    body["params"] = params
    head = {"Content-Type": "application/json", "A2A-Version": "1.0"}
    req = urllib.request.Request(url, json.dumps(body).encode(), head)
    return json.loads(urllib.request.urlopen(req).read())["result"]


# region: config
def config(hook, token, auth):
    cfg = {"url": hook, "token": token}
    if auth:  # "Bearer:hook-secret" → AuthenticationInfo
        scheme, _, cred = auth.partition(":")
        cfg["authentication"] = {"scheme": scheme, "credentials": cred}
    return cfg


# endregion


def main():
    p = argparse.ArgumentParser()
    for name in ("agent", "hook", "relay", "token"):
        p.add_argument(name)
    p.add_argument("--auth")
    a = p.parse_args()
    msg = {"messageId": "hook-1", "role": "ROLE_USER"}
    msg["parts"] = [{"data": BUS}]
    conf = {"returnImmediately": True}
    conf["taskPushNotificationConfig"] = config(a.hook, a.token, a.auth)
    task = rpc(
        a.agent, "SendMessage", {"message": msg, "configuration": conf}
    )
    tid = task["task"]["id"]
    print("SendMessage →", task["task"]["status"]["state"][11:])
    url = f"{a.relay}wait?task={tid}"  # 끝 알림 하나가 지나갈 때까지
    for r in json.loads(urllib.request.urlopen(url).read()):
        print(f"  {r['what']:<24} → {r['code']}")
    task = rpc(a.agent, "GetTask", {"id": tid, "historyLength": 0})
    print("GetTask →", task["status"]["state"][11:])


main()
# @ norun
