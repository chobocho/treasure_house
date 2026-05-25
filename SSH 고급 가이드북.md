# SSH 고급 가이드북 — 터널링과 실전 기법 완전 정복

> 본 가이드는 SSH 의 모든 면을 깊이 다룬다. 기초부터 시작해서 키 관리, 터널링, 점프 호스트, 인증서, 멀티플렉싱, SSHFS, sshuttle, mosh, Ansible/Git/CI 연동, 운영/보안/감사까지 한 권으로 정리한다. 모든 예제는 실제로 실행 가능하다.

---

## 목차

- [1장. SSH 의 본질](#1장-ssh-의-본질)
- [2장. 클라이언트 사용법 기초](#2장-클라이언트-사용법-기초)
- [3장. 키 인증 완전 정복](#3장-키-인증-완전-정복)
- [4장. ssh-agent 와 키 매니지먼트](#4장-ssh-agent-와-키-매니지먼트)
- [5장. ~/.ssh/config 의 모든 것](#5장-sshconfig-의-모든-것)
- [6장. 알려진 호스트와 호스트 키 검증](#6장-알려진-호스트와-호스트-키-검증)
- [7장. 포트 포워딩 — 로컬 (-L)](#7장-포트-포워딩--로컬--l)
- [8장. 포트 포워딩 — 원격 (-R)](#8장-포트-포워딩--원격--r)
- [9장. 포트 포워딩 — 동적 (-D, SOCKS)](#9장-포트-포워딩--동적--d-socks)
- [10장. ProxyJump 와 점프 호스트](#10장-proxyjump-와-점프-호스트)
- [11장. ProxyCommand 와 비표준 트랜스포트](#11장-proxycommand-와-비표준-트랜스포트)
- [12장. ControlMaster 멀티플렉싱](#12장-controlmaster-멀티플렉싱)
- [13장. SSH 인증서 (CA 기반 인증)](#13장-ssh-인증서-ca-기반-인증)
- [14장. 강제 명령 / 키 제약 / 봉인 환경](#14장-강제-명령--키-제약--봉인-환경)
- [15장. SCP / SFTP / rsync over SSH](#15장-scp--sftp--rsync-over-ssh)
- [16장. SSHFS — 원격 파일시스템 마운트](#16장-sshfs--원격-파일시스템-마운트)
- [17장. sshuttle — VPN 흉내내기](#17장-sshuttle--vpn-흉내내기)
- [18장. SSH-VPN — tun/tap 진짜 VPN](#18장-ssh-vpn--tuntap-진짜-vpn)
- [19장. X11 포워딩과 GUI 응용](#19장-x11-포워딩과-gui-응용)
- [20장. Agent 포워딩 — 안전하게 쓰는 법](#20장-agent-포워딩--안전하게-쓰는-법)
- [21장. Mosh — 끊어지지 않는 셸](#21장-mosh--끊어지지-않는-셸)
- [22장. SSH escape sequences](#22장-ssh-escape-sequences)
- [23장. Git over SSH](#23장-git-over-ssh)
- [24장. Ansible 과 SSH](#24장-ansible-과-ssh)
- [25장. CI/CD 에서의 SSH](#25장-cicd-에서의-ssh)
- [26장. 자동화 — expect, sshpass, paramiko](#26장-자동화--expect-sshpass-paramiko)
- [27장. SSH 서버 운영](#27장-ssh-서버-운영)
- [28장. PAM 과 2FA, FIDO2/U2F](#28장-pam-과-2fa-fido2u2f)
- [29장. 감사와 로깅](#29장-감사와-로깅)
- [30장. 보안 강화 (Hardening)](#30장-보안-강화-hardening)
- [31장. 트러블슈팅 패턴](#31장-트러블슈팅-패턴)
- [32장. Bastion 패턴과 Zero Trust](#32장-bastion-패턴과-zero-trust)
- [33장. 컨테이너 / Kubernetes 와 SSH](#33장-컨테이너--kubernetes-와-sshl)
- [34장. 종합 시나리오 워크북 (1–40)](#34장-종합-시나리오-워크북)
- [부록 A. 알고리즘과 암호 스위트](#부록-a-알고리즘과-암호-스위트)
- [부록 B. 주요 옵션 레퍼런스](#부록-b-주요-옵션-레퍼런스)
- [부록 C. 에러 메시지 사전](#부록-c-에러-메시지-사전)

---

# 1장. SSH 의 본질

## 1.1 왜 SSH 인가

SSH(Secure Shell)는 두 호스트 사이에 **인증된 암호 채널**을 만들고, 그 위에 **셸 세션**, **파일 전송**, **포트 포워딩**, **에이전트 포워딩** 같은 다중 기능을 다중화(multiplex)해 흘려보내는 프로토콜이다. 1995년 핀란드의 Tatu Ylönen 이 telnet/rlogin/rsh 의 평문 인증을 대체할 목적으로 만들었고, 이후 표준화된 SSH-2(RFC 4250–4256)가 사실상 모든 현대 구현의 기반이다.

OpenSSH 는 SSH-2 의 가장 널리 쓰이는 구현체로, OpenBSD 프로젝트에서 유지된다. 본 가이드는 OpenSSH 기준으로 작성한다.

## 1.2 SSH 의 3 계층

| 계층 | 역할 | RFC |
|---|---|---|
| Transport Layer | 키 교환, 서버 인증, 암호화, 무결성, 압축 | 4253 |
| User Authentication Layer | 사용자 인증 (publickey, password, keyboard-interactive, hostbased, gssapi) | 4252 |
| Connection Layer | 채널 다중화 (session, direct-tcpip, forwarded-tcpip 등) | 4254 |

핵심은 **Connection Layer 의 채널 다중화**다. 한 TCP 연결 위에서 셸, 여러 개의 포트 포워딩, 에이전트, X11 이 동시에 흐른다. 이 점이 SSH 를 단순 쉘 도구가 아니라 **범용 보안 트랜스포트**로 만든다.

## 1.3 핸드셰이크 한 줄 요약

```
TCP connect → Version exchange ("SSH-2.0-OpenSSH_9.6")
            → KEXINIT (지원 알고리즘 협상)
            → 키 교환 (ECDH/X25519/...) + 서버 호스트 키 서명 검증
            → NEWKEYS (대칭키로 전환)
            → ssh-userauth → ssh-connection
            → 채널 열기 (session/exec/subsystem/direct-tcpip/...)
```

서명 검증 단계가 곧 **호스트 키 신뢰**다. `~/.ssh/known_hosts` 또는 SSH CA 인증서가 여기서 쓰인다.

## 1.4 키 한 쌍 = 자격증명

서버 호스트 키, 사용자 키 모두 **공개키 한 쌍**이다. 차이는 *어디에 있는지* 와 *누가 신뢰하는지* 다.

- 서버 호스트 키: `/etc/ssh/ssh_host_*` — 클라이언트가 신뢰
- 사용자 키: `~/.ssh/id_*` — 서버가 `~/.ssh/authorized_keys` 로 신뢰

이걸 인증서로 한 번에 묶는 게 13장의 SSH CA 모델이다.

---

# 2장. 클라이언트 사용법 기초

## 2.1 첫 연결

```bash
ssh user@host
ssh user@host -p 2222
ssh -i ~/.ssh/id_ed25519 user@host
ssh -v user@host          # 디버그
ssh -vvv user@host        # 더 많은 디버그
```

`-v` 의 출력을 읽는 능력이 SSH 트러블슈팅의 90% 다.

## 2.2 명령 실행 모드

```bash
ssh user@host "uname -a"
ssh user@host "cat /etc/os-release; uptime"
ssh user@host -- ls -la                # -- 이후는 원격에서 그대로
```

여러 명령은 따옴표로 묶어 한 줄에 보낸다. `&&` 와 `||` 도 그대로 작동한다.

## 2.3 입력/출력 파이프

```bash
# 로컬 → 원격으로 흘리기
tar czf - ./project | ssh user@host "tar xzf - -C /tmp"

# 원격 → 로컬로 흘리기
ssh user@host "cat /var/log/syslog" | grep error | less

# 양쪽으로 동시에
ssh user@host "mysqldump -u root -p mydb" | ssh user@backup "cat > backup.sql"
```

이 패턴 하나만 익혀도 임시 파일과 SCP 가 70% 사라진다.

## 2.4 TTY 할당

`-t` 는 강제 TTY, `-T` 는 강제 비할당.

```bash
ssh -t user@host sudo systemctl restart nginx   # sudo 가 비밀번호 받으려면 -t
ssh -tt user@host                               # 스크립트 안에서 강제
ssh -T git@github.com                           # GitHub 가 셸을 안 주므로
```

TTY 가 없으면 `top`, `vim`, `sudo` 가 깨진다. 반대로 자동화에서는 `-T` 가 깔끔하다.

## 2.5 종료 코드와 파이프라인

```bash
ssh user@host "exit 42"; echo $?    # 42 — 원격 종료 코드가 그대로 전달됨
```

이걸 이용해 CI 에서 원격 명령의 성공/실패를 그대로 잡는다.

## 2.6 옵션을 명령행에서 덮어쓰기 — `-o`

```bash
ssh -o StrictHostKeyChecking=no \
    -o UserKnownHostsFile=/dev/null \
    -o ConnectTimeout=5 \
    user@host
```

`-o KEY=VALUE` 는 `~/.ssh/config` 의 어떤 항목이든 일회성으로 덮어쓴다.

## 2.7 자주 쓰는 한 줄 모음

```bash
# 빠른 connect 테스트
ssh -o ConnectTimeout=3 -o BatchMode=yes user@host true && echo OK

# 키 핑거프린트 보기 (서버 측)
ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub

# 클라이언트가 본 서버 핑거프린트
ssh-keyscan -t ed25519 host | ssh-keygen -lf -

# 모든 옵션을 적용해서 본 결과
ssh -G user@host | less
```

`ssh -G` 는 **실제 적용된 설정**을 모두 출력한다. config 디버깅의 핵심 무기다.

---

# 3장. 키 인증 완전 정복

## 3.1 알고리즘 선택

2026년 기준 권장:

| 알고리즘 | 키 크기 | 권장도 | 특징 |
|---|---|---|---|
| **ed25519** | 256-bit | ★★★★★ | 빠르고 짧고 안전. 기본 선택 |
| **ed25519-sk** | + FIDO2 | ★★★★★ | 하드웨어 키(YubiKey 등) 결합 |
| **ecdsa** | P-256/384/521 | ★★★ | NIST 곡선 — 정치적으로 회피하는 사람도 많음 |
| **rsa** | 4096+ | ★★★ | 호환성 위해서만 |
| **dsa** | — | ✗ | 사용 금지 |

## 3.2 키 생성

```bash
# 기본 (ed25519)
ssh-keygen -t ed25519 -C "you@host"

# 비밀번호 없이 (자동화용 — 신중)
ssh-keygen -t ed25519 -N "" -f ~/.ssh/automation

# RSA 4096 (필요할 때만)
ssh-keygen -t rsa -b 4096 -C "you@host"

# FIDO2 하드웨어 키
ssh-keygen -t ed25519-sk -O resident -O verify-required
```

`-O resident` 는 키 자체를 하드웨어에 저장해, 새 PC 에서도 `ssh-keygen -K` 로 복원할 수 있게 한다.

## 3.3 공개키 배포

```bash
ssh-copy-id user@host
ssh-copy-id -i ~/.ssh/id_ed25519.pub user@host
ssh-copy-id -p 2222 user@host

# 수동으로
cat ~/.ssh/id_ed25519.pub | ssh user@host "mkdir -p ~/.ssh && chmod 700 ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
```

권한이 너무 열려 있으면 sshd 는 키를 거절한다. 700 / 600 은 신성하다.

## 3.4 키 비밀번호 변경 / 코멘트 변경

```bash
ssh-keygen -p -f ~/.ssh/id_ed25519        # passphrase 변경
ssh-keygen -c -f ~/.ssh/id_ed25519        # comment 변경
ssh-keygen -y -f ~/.ssh/id_ed25519        # 공개키 재생성
```

마지막 명령은 공개키 파일을 잃어버렸을 때 개인키로부터 복원할 수 있어 자주 쓴다.

## 3.5 핑거프린트 비교

```bash
ssh-keygen -lf ~/.ssh/id_ed25519.pub
ssh-keygen -lf -E sha256 ~/.ssh/id_ed25519.pub
ssh-keygen -lvf ~/.ssh/id_ed25519.pub      # ASCII 아트
```

ASCII art (randomart) 는 사람의 시각 기억으로 핑거프린트 변화를 잡으라고 만든 기능이다. "어, 모양이 다른데?" 가 호스트 키 변조 신호일 수 있다.

## 3.6 authorized_keys 의 파워

```
# ~/.ssh/authorized_keys
# 단순 형식:
ssh-ed25519 AAAA... me@laptop

# 옵션 붙은 형식:
command="/usr/local/bin/backup-only.sh",no-pty,no-port-forwarding,no-X11-forwarding,no-agent-forwarding ssh-ed25519 AAAA... backup@laptop

# IP 제한:
from="10.0.0.0/8,192.168.1.0/24" ssh-ed25519 AAAA... me@vpn

# 여러 옵션 조합:
from="10.0.0.5",command="/usr/bin/git-shell",no-pty,no-port-forwarding ssh-ed25519 AAAA... ci@runner
```

이 한 줄로 강력한 권한 제어가 가능하다. 자세한 건 14장.

---

# 4장. ssh-agent 와 키 매니지먼트

## 4.1 ssh-agent 가 푸는 문제

비밀번호 걸린 키를 매번 풀기는 귀찮다. `ssh-agent` 는 한 번 푼 키를 메모리에 들고 있다가 SSH 가 요청하면 서명만 대신 해 준다. 개인키 자체는 소켓 너머로 나가지 않는다.

## 4.2 시작과 등록

```bash
# bash/zsh
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519
ssh-add -l                          # 등록된 키 목록
ssh-add -L                          # 공개키 형식으로
ssh-add -d ~/.ssh/id_ed25519        # 제거
ssh-add -D                          # 모두 제거
ssh-add -t 3600 ~/.ssh/id_ed25519   # 1시간 후 자동 만료
ssh-add -c ~/.ssh/id_ed25519        # 사용 시마다 확인 (askpass)
```

`-t` 와 `-c` 는 보안에 매우 중요하다. 자동화가 아닌 한 무한 보유는 피한다.

## 4.3 SSH_AUTH_SOCK

`ssh-agent` 가 만든 유닉스 도메인 소켓의 경로가 `$SSH_AUTH_SOCK` 에 들어간다. 자식 프로세스가 이걸 상속받기 때문에, 같은 셸에서 띄운 ssh 는 자동으로 agent 를 발견한다.

```bash
echo $SSH_AUTH_SOCK
# /tmp/ssh-XXXXXX/agent.NNNN
```

tmux/screen 안에서 agent 가 안 보이는 흔한 문제는 보통 이 변수가 stale 한 거다. 해결:

```bash
# ~/.zshrc 또는 ~/.bashrc
if [ -z "$SSH_AUTH_SOCK" ] && [ -S "$HOME/.ssh/agent.sock" ]; then
  export SSH_AUTH_SOCK="$HOME/.ssh/agent.sock"
fi

# 또는 systemd user 서비스로 항상 같은 경로
# ~/.config/systemd/user/ssh-agent.service 참조 (4.6)
```

## 4.4 1Password / Bitwarden / KeePassXC agent

요즘은 비밀번호 매니저가 직접 ssh-agent 인터페이스를 노출한다.

```bash
# 1Password
export SSH_AUTH_SOCK="$HOME/Library/Group Containers/2BUA8C4S2C.com.1password/t/agent.sock"

# KeePassXC
export SSH_AUTH_SOCK="$HOME/.local/share/keepassxc/keepassxc.sock"
```

장점: Touch ID/Face ID 로 키 사용을 게이팅할 수 있다.

## 4.5 윈도우의 OpenSSH agent

```powershell
Set-Service -Name ssh-agent -StartupType Automatic
Start-Service ssh-agent
ssh-add $env:USERPROFILE\.ssh\id_ed25519
```

## 4.6 systemd user 서비스로 영속화

`~/.config/systemd/user/ssh-agent.service`:

```ini
[Unit]
Description=SSH key agent

[Service]
Type=simple
Environment=SSH_AUTH_SOCK=%h/.ssh/agent.sock
ExecStart=/usr/bin/ssh-agent -D -a $SSH_AUTH_SOCK

[Install]
WantedBy=default.target
```

```bash
systemctl --user enable --now ssh-agent
echo 'export SSH_AUTH_SOCK="$HOME/.ssh/agent.sock"' >> ~/.zshrc
```

이러면 로그인 셸이든 cron 이든 한 곳에서 보고, 셸을 새로 띄울 때마다 `ssh-add` 안 해도 된다.

## 4.7 Confirmation 과 askpass

`ssh-add -c` 를 쓰려면 GUI 또는 콘솔 askpass 가 필요하다.

```bash
# 콘솔용
SSH_ASKPASS=/usr/lib/ssh/ssh-askpass SSH_ASKPASS_REQUIRE=force ssh-add -c key
```

각 사용 시 OS 가 다이얼로그를 띄운다. 보안↔편의 사이의 좋은 절충점이다.

---

# 5장. ~/.ssh/config 의 모든 것

## 5.1 첫 형식

```ssh
# ~/.ssh/config
Host alias
    HostName actual.host.example.com
    User myname
    Port 2222
    IdentityFile ~/.ssh/id_ed25519
    IdentitiesOnly yes
```

이제 `ssh alias` 만 치면 된다.

## 5.2 패턴 매칭

```ssh
Host *.internal
    User admin
    ProxyJump bastion

Host db-*
    User dba
    ForwardAgent no
    ServerAliveInterval 30

Host !secret-* *
    IdentityFile ~/.ssh/id_default
```

규칙 적용 순서: **위에서 아래로 모든 매칭 항목이 누적**되며, **먼저 정의된 값이 이긴다**. 그래서 일반 규칙은 아래에 둔다.

## 5.3 Match 블록 — 더 강력한 조건

```ssh
Match host *.prod exec "test $(hostname) = laptop"
    IdentityFile ~/.ssh/id_prod_only_on_laptop

Match user root
    PubkeyAuthentication yes
    PasswordAuthentication no

Match originalhost git.example.com user git
    IdentityFile ~/.ssh/id_git
    IdentitiesOnly yes
```

`Match exec "..."` 은 임의의 명령으로 조건을 만들 수 있어 위치/네트워크별 동적 설정이 가능하다.

## 5.4 Include — 설정 분할

```ssh
# ~/.ssh/config
Include ~/.ssh/config.d/*.conf
Include ~/.ssh/work/*
```

회사 / 개인 / 프로젝트별로 파일을 쪼개고, `.gitignore` 도 자유롭게 관리.

## 5.5 자주 쓰는 옵션 베스트 프랙티스

```ssh
Host *
    AddKeysToAgent yes
    UseKeychain yes              # macOS — Keychain 자동 연동
    IdentitiesOnly yes           # 이 호스트엔 IdentityFile 만 시도 (중요)
    HashKnownHosts yes
    StrictHostKeyChecking accept-new
    ServerAliveInterval 60
    ServerAliveCountMax 3
    ControlMaster auto
    ControlPath ~/.ssh/cm-%r@%h:%p
    ControlPersist 10m
    Compression no               # 빠른 망에서는 끄는 게 빠름
```

### IdentitiesOnly yes 는 왜 중요한가

agent 에 키가 10개 있으면 SSH 는 차례로 시도한다. 어떤 서버는 잘못된 키 시도가 6회 넘으면 IP 를 차단한다. `IdentitiesOnly yes` 는 "이 Host 블록에 명시된 IdentityFile 만 시도해라" 라는 의미다.

## 5.6 토큰

config 의 값은 토큰으로 치환된다.

| 토큰 | 의미 |
|---|---|
| `%h` | HostName |
| `%p` | Port |
| `%r` | 원격 사용자 |
| `%u` | 로컬 사용자 |
| `%d` | 로컬 홈 |
| `%n` | 명령행에 입력된 호스트 이름 |
| `%C` | `%l%h%p%r` 의 SHA-1 (ControlPath 길이 제한 회피) |

```ssh
ControlPath ~/.ssh/cm-%C
```

## 5.7 Hostname vs Host

- `Host`: 별칭 (별칭에 패턴 매칭 적용)
- `HostName`: 실제 DNS/IP

```ssh
Host prod
    HostName 10.20.30.40
```

`ssh prod` → 실제로는 10.20.30.40 으로 간다.

## 5.8 디버깅

```bash
ssh -G alias              # 적용된 설정 전부
ssh -F /dev/null host     # config 무시하고 기본만
ssh -F ./test_config host # 다른 config 사용
```

---

# 6장. 알려진 호스트와 호스트 키 검증

## 6.1 known_hosts 파일

```
# ~/.ssh/known_hosts
host.example.com,10.0.0.1 ssh-ed25519 AAAAC3...
|1|abc=|def= ssh-ed25519 AAAAC3...   # HashKnownHosts yes 일 때
```

## 6.2 처음 접속할 때

```
The authenticity of host 'foo (10.0.0.1)' can't be established.
ED25519 key fingerprint is SHA256:abcd1234...
Are you sure you want to continue connecting (yes/no/[fingerprint])?
```

이 시점에서 사용자가 진짜로 핑거프린트를 검증해야 한다. 수단:

- 클라우드 콘솔/메타데이터에서 호스트 키 확인 (AWS EC2 가 출력)
- DNS SSHFP 레코드
- SSH 인증서 (13장) — 이게 정답

## 6.3 SSHFP DNS 레코드

```
example.com. IN SSHFP 4 2 abcd1234ef...
```

`/etc/ssh/ssh_config` 에서:

```ssh
VerifyHostKeyDNS ask
```

DNSSEC 가 켜져 있으면 자동 신뢰까지 가능하다. 호스트 키 발급 시:

```bash
ssh-keygen -r host.example.com -f /etc/ssh/ssh_host_ed25519_key.pub
```

## 6.4 호스트 키가 바뀌었을 때

```
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@    WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!     @
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
```

진짜로 바뀐 거라면 (서버 재설치 등):

```bash
ssh-keygen -R host.example.com
ssh-keygen -R 10.0.0.1
```

해시되어 있어도 잘 동작한다. 절대 무지성으로 `StrictHostKeyChecking=no` 로 회피하지 말 것.

## 6.5 `ssh-keyscan` 으로 사전 적재

신규 머신을 자동화로 풀 때:

```bash
ssh-keyscan -t ed25519,rsa host1 host2 host3 >> ~/.ssh/known_hosts

# 이미 있는 항목과 비교만
ssh-keyscan -t ed25519 host | diff - <(grep host ~/.ssh/known_hosts)
```

CI 빌더라면 호스트 키 핑거프린트를 secrets 에 박아두고 매 실행 시 비교하는 게 가장 안전하다.

## 6.6 `accept-new`

```ssh
StrictHostKeyChecking accept-new
```

처음 보는 호스트는 자동 추가, 알려진 호스트의 변경은 거부. 인터랙티브가 거의 없는 사람에게 좋은 기본값이다.

---

# 7장. 포트 포워딩 — 로컬 (-L)

## 7.1 개념

```
[로컬:LP] ⇄ ssh ⇄ [원격]
                    └──→ TARGET:TP
```

로컬 포트 LP 로 들어오는 트래픽이 SSH 채널을 통해 원격에 도착한 뒤, 원격이 TARGET:TP 로 전달한다.

```bash
ssh -L LP:TARGET:TP user@gateway
```

여기서 TARGET 은 *원격이 본 시점의* 호스트다. `localhost` 면 원격 자기 자신, `db.internal` 이면 원격이 풀 수 있는 내부 DNS.

## 7.2 가장 흔한 예 — DB 접속

```bash
ssh -L 5432:localhost:5432 user@dbhost
psql -h 127.0.0.1 -p 5432 -U app mydb
```

`dbhost` 가 `localhost` 에서만 5432 를 열어둬도 문제없다.

## 7.3 게이트웨이를 거쳐 내부 DB

```bash
ssh -L 5432:db.internal.example:5432 user@bastion
```

bastion 은 5432 를 안 열어도 된다. bastion 의 SSH 데몬이 db.internal:5432 로 TCP 를 연다.

## 7.4 한 명령에 여러 -L

```bash
ssh -L 5432:db:5432 \
    -L 6379:cache:6379 \
    -L 9200:es:9200 \
    user@bastion
```

## 7.5 GatewayPorts — 다른 컴퓨터에도 노출

기본은 127.0.0.1 에만 바인딩한다. 같은 LAN 의 다른 사람도 쓰게 하려면:

```bash
ssh -L 0.0.0.0:8080:internal:80 user@bastion
ssh -g -L 8080:internal:80 user@bastion          # -g 도 동일 효과
```

config:

```ssh
Host bastion
    GatewayPorts yes
```

## 7.6 백그라운드, 명령 없이

```bash
ssh -fNL 5432:db:5432 user@bastion
# -f: 인증 후 백그라운드
# -N: 원격 명령 실행 안 함
# -L: 포트 포워딩
```

종료:

```bash
pgrep -af "ssh -fNL 5432"
kill <PID>

# 또는 ControlMaster 로 깔끔하게 (12장)
ssh -O cancel -L 5432:db:5432 bastion
```

## 7.7 유닉스 소켓 포워딩

```bash
ssh -L /tmp/local.sock:/var/run/docker.sock user@dockerhost
DOCKER_HOST=unix:///tmp/local.sock docker ps
```

원격의 Docker 데몬을 마치 로컬에 있는 것처럼 다룰 수 있다.

## 7.8 방향 헷갈림 방지

> **로컬 -L 은 "서비스를 내 쪽으로 끌고 온다"**
> **원격 -R 은 "서비스를 저 쪽으로 밀어 보낸다"**

이 한 줄만 외우면 된다.

---

# 8장. 포트 포워딩 — 원격 (-R)

## 8.1 개념

```
[로컬] ──→ TARGET:TP
            ↑
            └──┐
[원격:RP] ⇄ ssh ⇄ [로컬]
```

원격에 RP 포트가 열린다. 그쪽으로 누가 접속하면, SSH 가 트래픽을 내 로컬로 가져와서 TARGET:TP 로 보낸다.

```bash
ssh -R RP:TARGET:TP user@remote
```

## 8.2 NAT 뒤 노트북에 외부에서 접근하기

집 PC 에서:

```bash
ssh -fNR 0.0.0.0:2222:localhost:22 user@public-vps
```

이제 `public-vps:2222` 로 SSH 하면 사실은 우리 집 PC 의 22 로 연결된다.

VPS 의 sshd_config 에 다음 필요:

```
GatewayPorts yes      # 또는 clientspecified
```

`clientspecified` + `-R 0.0.0.0:2222:...` 가 가장 명시적이다.

## 8.3 로컬 웹 서비스 데모

```bash
# 로컬에서 8080 으로 데모 서버 실행 중
ssh -fNR 80:localhost:8080 user@public-vps
# 친구가 http://public-vps/ 로 접속
```

## 8.4 동적 -R 으로 점프

```bash
ssh -R 1080 user@remote          # 포트만 적으면 동적(SOCKS) 모드
```

원격에서 1080 으로 들어오면 그게 *내 로컬* 을 통해 SOCKS 프록시로 나간다. 9장의 -D 를 반대 방향으로 한 셈.

## 8.5 RemoteForward in config

```ssh
Host vps
    HostName 1.2.3.4
    RemoteForward 2222 localhost:22
    RemoteForward 8080 localhost:3000
    ExitOnForwardFailure yes
    ServerAliveInterval 30
    ServerAliveCountMax 3
```

`ExitOnForwardFailure yes` 는 포워딩 실패 시 SSH 자체를 끊어 자동 재시도 루프(systemd 등)에 넘긴다.

## 8.6 영구 reverse tunnel — autossh

```bash
sudo apt install autossh
autossh -M 0 -fN \
    -o "ServerAliveInterval 30" \
    -o "ServerAliveCountMax 3" \
    -o "ExitOnForwardFailure yes" \
    -R 2222:localhost:22 user@vps
```

`autossh` 는 SSH 가 죽으면 자동으로 다시 띄운다. systemd unit 으로 만들면 편하다 (8.7).

## 8.7 systemd 로 영구화

`/etc/systemd/system/reverse-tunnel.service`:

```ini
[Unit]
Description=Reverse SSH tunnel to VPS
After=network-online.target
Wants=network-online.target

[Service]
User=tunnel
Type=simple
Environment="AUTOSSH_GATETIME=0"
ExecStart=/usr/bin/autossh -M 0 -N \
    -o "ServerAliveInterval=30" \
    -o "ServerAliveCountMax=3" \
    -o "ExitOnForwardFailure=yes" \
    -o "StrictHostKeyChecking=accept-new" \
    -i /home/tunnel/.ssh/id_ed25519 \
    -R 2222:localhost:22 user@vps
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable --now reverse-tunnel
```

## 8.8 보안 주의

reverse tunnel 은 사실상 NAT 우회 백도어다. 방화벽 정책 관점에서:

1. VPS 에서 `RP` 는 무인증 접근 허용이 아니라, 그냥 원래 서비스의 인증을 그대로 쓴다.
2. 그래도 외부에 노출하려면 `RP` 는 `127.0.0.1` 로만 묶고, VPS 에서 추가로 접근 제어 (예: 로컬 nginx 인증 → 그 다음 127.0.0.1:RP).
3. `PermitOpen` (sshd_config) 으로 RP 의 목적지 화이트리스트.

---

# 9장. 포트 포워딩 — 동적 (-D, SOCKS)

## 9.1 개념

```bash
ssh -D 1080 user@bastion
```

로컬 1080 에 **SOCKS5 프록시**가 뜬다. 브라우저나 curl 이 그쪽으로 트래픽을 보내면 bastion 이 받아서 자기 네트워크에서 접속해 준다.

## 9.2 한 줄 SOCKS 프록시

```bash
ssh -fND 1080 user@bastion
```

브라우저 설정 → SOCKS5 → `127.0.0.1:1080` → 끝. 이제 모든 HTTP 가 bastion 의 IP 로 나간다. 카페 와이파이의 호기심에서 벗어나는 가장 간단한 방법.

## 9.3 curl, wget, git 도 SOCKS

```bash
curl -x socks5h://127.0.0.1:1080 https://internal.example/api
curl --socks5-hostname 127.0.0.1:1080 https://internal/  # DNS 도 원격으로
git config --global http.proxy socks5h://127.0.0.1:1080
ALL_PROXY=socks5h://127.0.0.1:1080 npm install
```

`socks5h` 의 h 는 **DNS 도 원격에서**. 내부 호스트 이름이 로컬에서 안 풀려도 동작한다.

## 9.4 시스템 전체 프록시 — proxychains

`/etc/proxychains.conf`:

```
strict_chain
proxy_dns
[ProxyList]
socks5  127.0.0.1 1080
```

```bash
proxychains4 nmap -sT -Pn 10.0.0.0/24    # 내부망 정찰 (감사 끝나기 전엔 합법성 확인)
proxychains4 ssh user@deeper.host         # SSH 안의 SSH
```

## 9.5 PAC (Proxy Auto-Config) 와 결합

특정 도메인만 SOCKS 로:

```javascript
function FindProxyForURL(url, host) {
    if (dnsDomainIs(host, ".internal.example.com")) {
        return "SOCKS5 127.0.0.1:1080";
    }
    return "DIRECT";
}
```

## 9.6 -D 한계

- **TCP 만**, UDP 안 됨 (SOCKS5 의 UDP ASSOCIATE 를 OpenSSH 가 지원하지 않음)
- DNS 는 socks5h 또는 PAC 로 명시해야 원격 해석
- ICMP / 핑은 안 됨

UDP 가 필요하면 sshuttle (17장) 또는 ssh-tun (18장).

---

# 10장. ProxyJump 와 점프 호스트

## 10.1 옛날 방식 — ProxyCommand 로 nc

```ssh
Host inner
    ProxyCommand ssh bastion -W %h:%p
```

`-W host:port` 는 stdin/stdout 을 SSH 채널로 연결한다. 그 위에 또 SSH 를 얹는다.

## 10.2 현대 방식 — ProxyJump (-J)

```bash
ssh -J bastion inner
ssh -J user1@bastion:22 user2@inner:2222
ssh -J b1,b2,b3 deepest                # 다단계
```

config:

```ssh
Host bastion
    HostName bastion.example.com
    User jumpuser

Host inner
    HostName 10.0.0.5
    User app
    ProxyJump bastion
```

`ssh inner` 한 번이면 bastion → inner 까지 자동.

## 10.3 다단계

```ssh
Host stage1
    HostName edge.example
    User edge

Host stage2
    HostName 10.10.10.10
    User mid
    ProxyJump stage1

Host target
    HostName 192.168.50.5
    User app
    ProxyJump stage2
```

`ssh target` → edge → 10.10.10.10 → 192.168.50.5.

## 10.4 키는 어디에 있어야 하나

ProxyJump 는 **각 단계의 키가 *내 로컬* 에 있어야 한다**. agent forwarding 을 안 써도 되도록 만든 게 ProxyJump 의 핵심 가치다. 보안 면에서 -A 보다 우월하다.

## 10.5 SCP 와 ProxyJump

옛 scp:

```bash
scp -o ProxyJump=bastion file.txt inner:~/
```

OpenSSH 9 이후의 scp 는 SFTP 모드를 쓰며 -J 를 직접 받는다:

```bash
scp -J bastion file.txt inner:~/
```

## 10.6 rsync 와 ProxyJump

```bash
rsync -av -e "ssh -J bastion" ./src/ inner:/srv/app/
```

## 10.7 멀티 점프 + 동시 멀티플렉싱

```ssh
Host *
    ControlMaster auto
    ControlPath ~/.ssh/cm-%C
    ControlPersist 10m
```

이러면 첫 호출에서 bastion 까지 한 번만 인증하고, 두 번째 호출은 그 채널을 재사용한다.

---

# 11장. ProxyCommand 와 비표준 트랜스포트

## 11.1 임의의 트랜스포트로 SSH 흘리기

`ProxyCommand` 는 stdin/stdout 으로 SSH 페이로드를 주고받는 어떤 명령이든 받는다.

## 11.2 corkscrew — HTTP CONNECT 프록시 통과

회사 방화벽이 SSH 포트를 막고 HTTP 프록시만 열어둔 경우:

```ssh
Host github-via-corp
    HostName github.com
    User git
    ProxyCommand corkscrew proxy.corp 8080 %h %p
```

## 11.3 cloudflared — Cloudflare Access 통과

```ssh
Host my-cf
    HostName ssh.example.com
    ProxyCommand cloudflared access ssh --hostname %h
```

## 11.4 AWS SSM Session Manager

EC2 인스턴스를 22 포트 노출 없이 SSH:

```ssh
Host i-*
    User ec2-user
    ProxyCommand sh -c "aws ssm start-session --target %h \
        --document-name AWS-StartSSHSession --parameters portNumber=%p"
```

```bash
ssh i-0abc123def456789
```

## 11.5 Azure / GCP

```ssh
# GCP IAP
Host gcp-*
    ProxyCommand gcloud compute start-iap-tunnel %h %p --listen-on-stdin

# Azure Bastion (developer 모드)
Host az-*
    ProxyCommand az network bastion tunnel --name BASTION --target-resource-id %h ...
```

## 11.6 Tor

```ssh
Host hidden
    HostName abcd1234efgh5678.onion
    ProxyCommand nc -X 5 -x 127.0.0.1:9050 %h %p
```

## 11.7 socat 으로 원하는 트랜스포트

```ssh
Host weird
    HostName backend
    ProxyCommand socat - OPENSSL:%h:%p,verify=1,cafile=/etc/ssl/ca.pem
```

SSH-in-TLS 같은 변종도 가능.

---

# 12장. ControlMaster 멀티플렉싱

## 12.1 왜 필요한가

매 SSH 호출마다 TCP + KEX + 인증 = 200~800ms. 여러 명령을 빠르게 돌리거나, ProxyJump 가 깊으면 누적된다. 멀티플렉싱은 첫 연결만 하고 나머지는 같은 채널을 공유한다.

## 12.2 설정

```ssh
Host *
    ControlMaster auto
    ControlPath ~/.ssh/cm-%C
    ControlPersist 10m
```

- `auto`: 마스터가 있으면 재사용, 없으면 만들기
- `%C`: HostName/Port/User 의 SHA-1 해시 (소켓 경로 길이 제한 회피)
- `ControlPersist`: 마지막 클라이언트가 끝난 뒤 마스터를 얼마나 유지할지

## 12.3 강제 마스터 / 슬레이브

```bash
ssh -M -fN host          # 마스터만 명시적으로 띄우기
ssh -S ~/.ssh/cm-%C host # 슬레이브 — 보통은 자동
```

## 12.4 마스터 제어 — `-O`

```bash
ssh -O check host                 # 살아있나?
ssh -O exit host                  # 종료
ssh -O stop host                  # 새 슬레이브 거부 (기존은 유지)
ssh -O forward -L 8080:db:5432 host   # 동작 중에 포워딩 추가
ssh -O cancel -L 8080:db:5432 host    # 포워딩 제거
```

이게 **SSH 의 숨겨진 슈퍼파워**다. 한 번 띄운 세션에 동적으로 -L/-R 을 붙였다 떼었다 한다.

## 12.5 자동화/CI 의 함정

CI 에서 ControlMaster 켜면 병렬 잡이 같은 socket 을 두고 다투다 깨진다. CI 에서는 명시적으로 끄거나 `ControlPath` 를 잡 ID 로 분리한다:

```bash
ssh -o ControlMaster=no -o ControlPath=none host
```

## 12.6 대규모 변경

수백 호스트를 도는 스크립트라면, 미리 `ControlMaster` 로 모든 호스트에 마스터를 띄우고 시작하면 전체 시간이 극적으로 줄어든다.

```bash
for h in $(cat hosts.txt); do
    ssh -o ControlMaster=auto -o ControlPersist=1h -fN $h
done

for h in $(cat hosts.txt); do
    ssh $h "uptime"
done
```

---

# 13장. SSH 인증서 (CA 기반 인증)

## 13.1 왜 인증서인가

키 분배의 두 가지 영원한 문제:

1. 사용자 키를 모든 서버의 `authorized_keys` 에 뿌려야 함
2. 서버 호스트 키를 모든 사용자의 `known_hosts` 에 뿌려야 함

CA 가 이걸 한 번에 해결한다. CA 키 한 쌍을 만들어 양쪽이 신뢰하면, **서명된 짧은 인증서**만 발급/회전하면 된다.

## 13.2 CA 키 생성

```bash
# 사용자 CA
ssh-keygen -t ed25519 -f user_ca -C "user-ca"

# 호스트 CA
ssh-keygen -t ed25519 -f host_ca -C "host-ca"
```

CA 키는 **절대로 일상 SSH 에 쓰지 않는다**. HSM/Vault 에 넣는다.

## 13.3 사용자 인증서 발급

```bash
ssh-keygen -s user_ca \
    -I "alice@2026-05-07" \
    -n alice,deploy \
    -V +8h \
    ~/alice/.ssh/id_ed25519.pub
```

- `-I` identity (감사 로그용)
- `-n` 허용 principals (리눅스 사용자명)
- `-V +8h` 8시간 유효
- 결과: `id_ed25519-cert.pub`

검사:

```bash
ssh-keygen -L -f id_ed25519-cert.pub
```

## 13.4 서버 측 신뢰 설정

`/etc/ssh/sshd_config`:

```
TrustedUserCAKeys /etc/ssh/user_ca.pub
```

또는 사용자별로 `~/.ssh/authorized_keys` 에:

```
cert-authority,principals="alice,deploy" ssh-ed25519 AAAA...user_ca
```

이제 alice 의 키 자체가 서버에 없어도, 인증서를 가진 alice 라면 통과.

## 13.5 호스트 인증서 발급

```bash
ssh-keygen -s host_ca \
    -I "web01.example.com" \
    -n web01.example.com,web01,10.0.0.5 \
    -V +52w \
    -h \
    /etc/ssh/ssh_host_ed25519_key.pub
```

`-h` 가 호스트 인증서를 의미. 결과를 `/etc/ssh/ssh_host_ed25519_key-cert.pub` 로 두고 sshd_config:

```
HostCertificate /etc/ssh/ssh_host_ed25519_key-cert.pub
```

## 13.6 클라이언트 측 호스트 CA 신뢰

`~/.ssh/known_hosts` 에 한 줄:

```
@cert-authority *.example.com,10.0.0.* ssh-ed25519 AAAA...host_ca
```

이제 example.com 의 어떤 서버를 처음 봐도, 호스트 인증서가 host_ca 로 서명만 되어 있으면 자동 신뢰.

## 13.7 OPTIONS / 강제 명령

```bash
ssh-keygen -s user_ca \
    -I "ci-runner" \
    -n deploy \
    -O force-command="/usr/local/bin/deploy.sh" \
    -O no-port-forwarding \
    -O no-pty \
    -V +1h \
    runner.pub
```

이 인증서를 받은 사람은 이 한 명령만 실행 가능. 14장 참조.

## 13.8 회전 / 폐기

폐기 목록:

```bash
ssh-keygen -k -f revoked-keys -s user_ca alice-old.pub
```

sshd_config:

```
RevokedKeys /etc/ssh/revoked-keys
```

또는 그냥 `-V` 를 짧게(8h) 쓰고 그것대로 만료시키는 게 가장 깔끔.

## 13.9 Vault / Smallstep 으로 자동화

HashiCorp Vault `ssh-cert` secret engine, Smallstep `step-ca`, Teleport, BastionZero 가 모두 위 메커니즘을 자동화한다. 핵심 흐름:

1. 사용자가 SSO 로 인증
2. CA 가 짧은 (수십 분) 인증서 발급
3. SSH 가 그걸로 접속
4. 만료되면 다시 발급

서버는 CA 공개키만 알고, 사용자 키 분배는 사라진다.

---

# 14장. 강제 명령 / 키 제약 / 봉인 환경

## 14.1 force-command

`authorized_keys`:

```
command="/usr/local/bin/git-shell-or-die",no-pty,no-port-forwarding,no-X11-forwarding,no-agent-forwarding,no-user-rc ssh-ed25519 AAAA... ci@runner
```

이 키로 들어오면 무엇을 입력하든 항상 그 명령만 실행된다. 원래 명령은 `$SSH_ORIGINAL_COMMAND` 환경변수로 전달.

```bash
#!/bin/bash
# /usr/local/bin/git-shell-or-die
case "$SSH_ORIGINAL_COMMAND" in
    "git-upload-pack "* | "git-receive-pack "*)
        exec $SSH_ORIGINAL_COMMAND
        ;;
    *)
        echo "denied"
        exit 1
        ;;
esac
```

## 14.2 백업 전용 키 — rrsync

```
command="/usr/bin/rrsync -ro /srv/data",restrict ssh-ed25519 AAAA... backup@laptop
```

`rrsync` 는 rsync 와 같이 오는 perl 스크립트. read-only / 특정 경로로만 rsync 를 강제한다.

`restrict` 키워드 (OpenSSH 7.2+) 는 모든 forwarding/pty/agent 를 한 번에 끈다.

## 14.3 IP 제한

```
from="10.0.0.0/8,!10.99.0.0/16,*.trusted.com" ssh-ed25519 AAAA... me
```

부정(`!`) 도 가능.

## 14.4 expiry-time

OpenSSH 8.2+:

```
expiry-time="20260607",restrict ssh-ed25519 AAAA... contractor
```

날짜 지나면 자동 거절.

## 14.5 chroot SFTP

`/etc/ssh/sshd_config`:

```
Match Group sftp-only
    ChrootDirectory /srv/sftp/%u
    ForceCommand internal-sftp
    AllowTcpForwarding no
    X11Forwarding no
```

`/srv/sftp/<user>` 는 root 소유, 0755. 그 안에 사용자 쓰기 가능 디렉터리를 둔다. 안 그러면 sshd 가 거부.

## 14.6 ForceCommand on sshd_config

```
Match User backup
    ForceCommand /usr/local/bin/backup-only.sh
    PermitTTY no
    AllowTcpForwarding no
```

## 14.7 PermitOpen / PermitListen

원격 포워딩 목적지/리스닝 포트를 화이트리스트:

```
Match User dev
    PermitOpen 10.0.0.5:5432 10.0.0.6:6379
    PermitListen 127.0.0.1:8000-8100
```

---

# 15장. SCP / SFTP / rsync over SSH

## 15.1 scp 의 운명

OpenSSH 9 부터 `scp` 는 내부적으로 SFTP 프로토콜을 쓴다 (`-O` 로 옛 SCP 도 가능). 그래도 인터페이스는 그대로.

```bash
scp file.txt user@host:/tmp/
scp user@host:/tmp/file.txt .
scp -r ./dir user@host:/srv/
scp -P 2222 file user@host:.        # 대문자 P (ssh 와 다름!)
scp -3 src@A:/x dst@B:/y            # A→로컬→B (직접 안 거치고)
scp -i key.pem -J bastion file inner:.
```

## 15.2 sftp — 인터랙티브

```bash
sftp user@host
> ls
> cd /var/log
> get -r nginx
> put localfile.txt
> bye

# 배치 모드
sftp -b commands.txt user@host
```

`commands.txt`:

```
cd /uploads
put *.csv
chmod 644 *.csv
bye
```

## 15.3 rsync — 가장 강력

```bash
rsync -avz ./src/ user@host:/dst/      # 표준 동기화
rsync -avzP ./big.iso user@host:/dst/  # 진행률
rsync -av --delete ./src/ user@host:/dst/   # 미러
rsync -av -e "ssh -p 2222 -i key" ./ user@host:/dst/
rsync -av --exclude='node_modules' --exclude='.git' ./ host:/dst/
rsync -av --include='*.py' --exclude='*' ./ host:/dst/
```

## 15.4 부분 전송 / 재개

```bash
rsync --partial --progress --append-verify ./big user@host:/dst/
```

대용량 파일이 끊기면 끊긴 자리부터 이어 받는다.

## 15.5 ssh 옵션 한 번에 — `-e`

```bash
rsync -av -e "ssh -J bastion -o ControlMaster=auto -o ControlPath=~/.ssh/cm-%C" \
    ./big-dir/ remote:/dst/
```

ControlMaster 와 결합하면 수많은 작은 파일도 빠르다 (각 연결 비용 ~0).

## 15.6 양방향 동기화 — unison

rsync 는 한쪽이 source. 양쪽 변경을 합치려면 `unison`:

```bash
unison ./local ssh://host//remote
```

## 15.7 큰 디렉터리 빠르게

작은 파일 수십만 개라면 tar 로 한 번에 흘리는 게 빠르다:

```bash
( cd src && tar cf - . ) | ssh host "cd /dst && tar xf -"

# 압축 + 진행률
tar cf - ./src | pv | ssh host "tar xf - -C /dst"
```

## 15.8 SFTP 서브시스템 강화

`/etc/ssh/sshd_config`:

```
Subsystem sftp internal-sftp
```

`internal-sftp` 는 외부 바이너리 없이 sshd 안에서 처리. 14.5 의 chroot 와 함께 안전.

---

# 16장. SSHFS — 원격 파일시스템 마운트

## 16.1 설치

```bash
# Debian/Ubuntu
sudo apt install sshfs

# macOS
brew install macfuse sshfs
```

## 16.2 마운트

```bash
mkdir -p ~/mnt/host
sshfs user@host:/srv/data ~/mnt/host \
    -o reconnect,ServerAliveInterval=15,ServerAliveCountMax=3,follow_symlinks
```

## 16.3 캐시 옵션 — 속도가 다른 차원

```bash
sshfs user@host:/big ~/mnt \
    -o cache=yes,kernel_cache,compression=no,Ciphers=aes128-gcm@openssh.com,large_read,big_writes
```

작은 파일을 IDE 가 수천번 stat 하는 걸 감내하려면 `kernel_cache` 가 필수.

## 16.4 언마운트

```bash
fusermount3 -u ~/mnt/host          # Linux
diskutil unmount ~/mnt/host        # macOS
```

## 16.5 systemd 자동 마운트

`/etc/fstab`:

```
user@host:/srv/data /home/me/mnt fuse.sshfs noauto,x-systemd.automount,_netdev,IdentityFile=/home/me/.ssh/id_ed25519,allow_other,reconnect 0 0
```

처음 접근할 때만 자동 마운트.

---

# 17장. sshuttle — VPN 흉내내기

## 17.1 컨셉

`-D` 는 SOCKS, 앱이 SOCKS 알아야 함. **sshuttle** 은 로컬에서 iptables/PF 로 트래픽을 가로채 SSH 너머로 흘린다. 앱은 아무것도 모른다. UDP DNS 도 처리.

## 17.2 설치 / 사용

```bash
pip install --user sshuttle      # 또는 apt/brew

sshuttle -r user@bastion 10.0.0.0/8 192.168.0.0/16
sshuttle -r user@bastion 0/0     # 모든 트래픽
sshuttle -r user@bastion --dns 10.0.0.0/8     # DNS 도 원격
sshuttle -r user@bastion -x 10.0.0.5 10.0.0.0/8   # 일부 제외
```

## 17.3 요구 사항

- 로컬: root (sudo)
- 원격: Python 만 있으면 됨. 권한 불필요.

이 점이 거대한 차이다. 회사 bastion 에 root 없이도 VPN 처럼 쓴다.

## 17.4 latency 와 비교

- `-D` (SOCKS): 빠름, TCP 만, 앱 호환성 이슈
- sshuttle: 좀 느림, TCP+DNS, 모든 앱 OK
- 진짜 VPN (WireGuard): 빠름, UDP/ICMP 다 됨, 단 서버 협조 필요

## 17.5 활용 — kube DNS 만 원격으로

```bash
sshuttle -r user@bastion --dns -x 0/0 10.96.0.0/12
```

cluster IP 만 우회. 나머지 트래픽은 로컬로.

---

# 18장. SSH-VPN — tun/tap 진짜 VPN

## 18.1 OpenSSH 의 `-w`

OpenSSH 자체에 layer-3 VPN 이 들어 있다. 거의 안 쓰지만 알면 멋지다.

서버 sshd_config:

```
PermitTunnel yes
```

서버 측 root 로:

```bash
ssh -fN -w 0:0 user@host
ip addr add 10.99.0.1/30 peer 10.99.0.2 dev tun0
ip link set tun0 up
```

원격 (post-login 으로 자동화):

```bash
ip addr add 10.99.0.2/30 peer 10.99.0.1 dev tun0
ip link set tun0 up
```

이제 10.99.0.0/30 으로 두 호스트가 라우팅 가능. 라우팅 테이블에 적절히 넣으면 진짜 VPN.

## 18.2 한계

- TCP-over-TCP. UDP/실시간엔 약함.
- 양쪽 root 권한.
- WireGuard 가 더 빠르고 깔끔.

## 18.3 그래도 쓰는 경우

- 서버에 OpenSSH 외엔 절대 못 까는 환경
- 1회성 진단용 ICMP

---

# 19장. X11 포워딩과 GUI 응용

## 19.1 켜기

서버:

```
X11Forwarding yes
X11DisplayOffset 10
X11UseLocalhost yes
```

클라이언트:

```bash
ssh -X user@host        # trusted 검사 약함
ssh -Y user@host        # trusted (보안 약함, 호환성 좋음)
```

원격에서:

```bash
xeyes
xterm
firefox &
```

## 19.2 macOS / Windows

- macOS: XQuartz 설치 필요
- Windows: VcXsrv / X410 / Microsoft WSLg

## 19.3 wayland 시대의 대안

- `waypipe` — Wayland 앱을 SSH 너머로 (-X 의 wayland 버전)
- VNC over SSH 터널 (`-L 5901:localhost:5901`)
- RDP over SSH

```bash
waypipe ssh user@host weston-terminal
```

## 19.4 보안

X11 forwarding 은 본질적으로 keylogger 가능성이 있다 (서버가 클라이언트 X 서버에 키보드/스크린 접근). 신뢰할 수 없는 호스트엔 절대 -Y 금지.

---

# 20장. Agent 포워딩 — 안전하게 쓰는 법

## 20.1 작동

```bash
ssh -A user@hop
hop$ ssh another        # hop 의 ssh 가 *내 로컬 agent* 에게 서명을 요청
```

`-A` 는 hop 머신에 가짜 agent 소켓을 만들고, 그쪽 요청을 SSH 채널로 내 로컬 agent 에 전달한다.

## 20.2 위험

`hop` 의 root 는 그 가짜 소켓을 통해 **나 모르게** 다른 곳에 SSH 할 수 있다. 키 자체는 안 새지만 서명을 시킬 수 있다.

## 20.3 안전 대안

1. **ProxyJump 가 거의 항상 답이다.** agent 를 hop 에 노출하지 않고도 다단계 SSH 가능.
2. agent forwarding 이 정말 필요하면 `ssh-add -c` 로 사용 시마다 확인.
3. config 에서 호스트별로 켠다:

```ssh
Host trusted-hop
    ForwardAgent yes

Host *
    ForwardAgent no
```

## 20.4 sshd 측 제한

```
AllowAgentForwarding no
```

또는 `Match Group` 으로 특정 그룹만.

---

# 21장. Mosh — 끊어지지 않는 셸

## 21.1 무엇

Mosh = Mobile shell. 첫 인증만 SSH 로 하고 그 뒤는 UDP 의 SSP 프로토콜로 통신. 모바일 망 변경, 슬립 후 재개에서도 끊기지 않음.

## 21.2 사용

```bash
sudo apt install mosh
mosh user@host
mosh --ssh="ssh -J bastion -i ~/.ssh/id_ed25519" user@host
mosh -p 60000 user@host          # UDP 포트 고정
```

서버에 mosh-server 가 있어야 함. 방화벽에서 60000-61000/udp 열기.

## 21.3 한계

- 스크롤백 기본 안 됨 (tmux 와 같이 쓰는 게 정답)
- 서버 컴포넌트 필요 (모든 서버에 깔 수 없을 수도)

---

# 22장. SSH escape sequences

세션 안에서 `~` (줄 처음) + 문자로 ssh 자체와 대화한다.

| 시퀀스 | 동작 |
|---|---|
| `~.` | 즉시 끊기 |
| `~^Z` | ssh 를 백그라운드로 (Ctrl-Z) |
| `~~` | 리터럴 `~` |
| `~#` | 포워딩된 연결 목록 |
| `~&` | 백그라운드 분리 (포워딩 유지) |
| `~?` | 도움말 |
| `~C` | 명령 모드 (포워딩 추가/취소) |
| `~R` | rekey 강제 |
| `~B` | BREAK 전송 (시리얼) |
| `~V` `/` `~v` | 로그 레벨 증감 |

`~C` 의 명령:

```
ssh> -L 9090:localhost:9090
ssh> -KR 8080
ssh> help
```

세션 안에서 동적으로 포워딩을 켰다 껐다 한다.

---

# 23장. Git over SSH

## 23.1 GitHub 멀티 계정

```ssh
Host github-personal
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_personal
    IdentitiesOnly yes

Host github-work
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_work
    IdentitiesOnly yes
```

리모트:

```bash
git clone git@github-work:org/repo.git
git remote set-url origin git@github-personal:me/repo.git
```

## 23.2 deploy key vs user key

- deploy key: 한 리포에만 묶인 키. 서버에 두기 안전.
- user key: 사용자 권한 전체. 노트북에 둠.

서버에는 deploy key 만 두는 게 원칙.

## 23.3 ssh signing 으로 커밋 서명

```bash
git config --global gpg.format ssh
git config --global user.signingkey ~/.ssh/id_ed25519.pub
git config --global commit.gpgsign true
```

GPG 없이도 SSH 키로 커밋 서명. GitHub 도 검증한다.

## 23.4 git push -e ssh 옵션 덮어쓰기

```bash
GIT_SSH_COMMAND="ssh -i ~/.ssh/special -o IdentitiesOnly=yes" git push
```

## 23.5 host alias 로 모노레포 보호

회사 GitHub 만 ProxyJump 거치게:

```ssh
Host gh-corp
    HostName ssh.github.com
    User git
    Port 443
    ProxyJump bastion-corp
    IdentityFile ~/.ssh/id_corp
    IdentitiesOnly yes
```

```bash
git remote set-url origin git@gh-corp:org/repo.git
```

---

# 24장. Ansible 과 SSH

## 24.1 인벤토리

```ini
# inventory.ini
[web]
web1.example.com
web2.example.com

[web:vars]
ansible_user=ubuntu
ansible_ssh_private_key_file=~/.ssh/id_deploy
ansible_ssh_common_args='-o ControlMaster=auto -o ControlPersist=60s -J bastion'
```

## 24.2 ansible.cfg

```ini
[ssh_connection]
ssh_args = -C -o ControlMaster=auto -o ControlPersist=60s
pipelining = True
control_path = ~/.ssh/ansible-cm-%%C
```

`pipelining = True` + sudo with NOPASSWD = 속도 3-5배.

## 24.3 점프 호스트

`ansible_ssh_common_args='-o ProxyJump=bastion'` 또는 ssh config 에 ProxyJump 박는다.

## 24.4 호스트 키 자동 채우기

```bash
ansible all -i inv -m raw -a "uptime" \
    -e 'ansible_ssh_common_args="-o StrictHostKeyChecking=accept-new"'
```

## 24.5 vault 키와 SSH 인증서 결합

CI 가 vault 에서 짧은 SSH 인증서를 받아 `ansible_ssh_extra_args="-i /tmp/cert"` 로 주는 패턴이 가장 현대적이다 (13.9 와 결합).

---

# 25장. CI/CD 에서의 SSH

## 25.1 secrets 에 키 저장

GitHub Actions:

```yaml
- name: Deploy
  uses: appleboy/ssh-action@v1
  with:
    host: ${{ secrets.HOST }}
    username: deploy
    key: ${{ secrets.SSH_PRIVATE_KEY }}
    script: |
      cd /srv/app && git pull && systemctl restart app
```

## 25.2 호스트 키 핀 박기

```yaml
- run: |
    mkdir -p ~/.ssh
    echo "${{ secrets.HOST_FINGERPRINT }}" >> ~/.ssh/known_hosts
    chmod 600 ~/.ssh/known_hosts
```

`StrictHostKeyChecking=yes` 로 둘 것. `accept-new` 는 첫 빌드 때 MITM 받는 짧은 창을 만든다.

## 25.3 deploy key 에 force-command

CI 키는 `command="/srv/deploy.sh",restrict` 로 묶어 셸을 못 얻게.

## 25.4 SSH 인증서 + OIDC

GitHub OIDC → Vault → SSH cert → SSH. 키가 디스크에 영구 존재 안 함. 짧은 만료. 가장 안전.

---

# 26장. 자동화 — expect, sshpass, paramiko

## 26.1 sshpass — 비밀번호를 명령행에서

```bash
sshpass -p 'P@ssw0rd' ssh user@host
SSHPASS='P@ssw0rd' sshpass -e ssh user@host
sshpass -f password.txt ssh user@host
```

레거시 시스템 마이그레이션용. **운영에선 키 인증 쓰자.**

## 26.2 expect

```tcl
#!/usr/bin/expect -f
set timeout 30
spawn ssh user@host
expect "password:"
send "P@ssw0rd\r"
expect "$ "
send "uptime\r"
expect "$ "
send "exit\r"
```

대화형 라우터/스위치 자동화의 마지막 도구.

## 26.3 paramiko (Python)

```python
import paramiko

key = paramiko.Ed25519Key.from_private_key_file("~/.ssh/id_ed25519")
client = paramiko.SSHClient()
client.load_system_host_keys()
client.set_missing_host_key_policy(paramiko.RejectPolicy())
client.connect("host", username="user", pkey=key)

stdin, stdout, stderr = client.exec_command("uname -a; uptime")
print(stdout.read().decode())

# SFTP
sftp = client.open_sftp()
sftp.put("local.tgz", "/tmp/local.tgz")
sftp.close()

client.close()
```

## 26.4 fabric

```python
from fabric import Connection

c = Connection("user@host", connect_kwargs={"key_filename": "~/.ssh/id"})
c.run("uname -a")
c.put("local.tgz", "/tmp/")

# 그룹
from fabric import ThreadingGroup
g = ThreadingGroup("h1", "h2", "h3", user="ubuntu")
g.run("uptime")
```

## 26.5 Go ssh 라이브러리

```go
package main

import (
    "log"
    "io/ioutil"
    "golang.org/x/crypto/ssh"
)

func main() {
    key, _ := ioutil.ReadFile("/home/me/.ssh/id_ed25519")
    signer, _ := ssh.ParsePrivateKey(key)

    cfg := &ssh.ClientConfig{
        User: "user",
        Auth: []ssh.AuthMethod{ssh.PublicKeys(signer)},
        HostKeyCallback: ssh.FixedHostKey(hostKey),
    }

    cli, err := ssh.Dial("tcp", "host:22", cfg)
    if err != nil { log.Fatal(err) }
    sess, _ := cli.NewSession()
    defer sess.Close()
    out, _ := sess.CombinedOutput("uname -a")
    log.Println(string(out))
}
```

## 26.6 parallel-ssh / pssh

```bash
pssh -h hosts.txt -i "uptime"
pssh -h hosts.txt -P -t 30 -i "apt-get update"
```

수백 호스트 동시 명령에 빠르다. ControlMaster 가 자동으로 도와준다.

---

# 27장. SSH 서버 운영

## 27.1 sshd_config 핵심 옵션

```
# /etc/ssh/sshd_config
Port 22
AddressFamily any
ListenAddress 0.0.0.0

Protocol 2
HostKey /etc/ssh/ssh_host_ed25519_key
HostKey /etc/ssh/ssh_host_rsa_key

KexAlgorithms curve25519-sha256@libssh.org,curve25519-sha256,diffie-hellman-group16-sha512,diffie-hellman-group18-sha512
Ciphers chacha20-poly1305@openssh.com,aes256-gcm@openssh.com,aes128-gcm@openssh.com
MACs hmac-sha2-512-etm@openssh.com,hmac-sha2-256-etm@openssh.com,umac-128-etm@openssh.com
HostKeyAlgorithms ssh-ed25519,rsa-sha2-512,rsa-sha2-256

LogLevel VERBOSE
SyslogFacility AUTH

PermitRootLogin prohibit-password
PubkeyAuthentication yes
PasswordAuthentication no
ChallengeResponseAuthentication no
KbdInteractiveAuthentication no
UsePAM yes
PermitEmptyPasswords no
MaxAuthTries 3
MaxSessions 10
LoginGraceTime 30

AllowUsers alice bob deploy
AllowGroups ssh-users
DenyUsers root nobody

ClientAliveInterval 60
ClientAliveCountMax 3

X11Forwarding no
AllowTcpForwarding yes
GatewayPorts no
PermitTunnel no
PrintMotd no
Banner /etc/ssh/banner

Subsystem sftp internal-sftp

UseDNS no
GSSAPIAuthentication no

# 인증서
TrustedUserCAKeys /etc/ssh/user_ca.pub
HostCertificate /etc/ssh/ssh_host_ed25519_key-cert.pub
RevokedKeys /etc/ssh/revoked-keys

Match Group sftp-only
    ChrootDirectory /srv/sftp/%u
    ForceCommand internal-sftp
    AllowTcpForwarding no

Match Address 10.0.0.0/8
    PasswordAuthentication yes
```

## 27.2 변경 후 검증

```bash
sshd -t                 # config 문법 검사
sshd -T | grep -i ciphers   # 적용된 값
systemctl reload ssh    # 또는 sshd
```

**reload 전에 다른 SSH 세션은 열어둘 것.** 망치면 lockout.

## 27.3 호스트 키 생성/회전

```bash
ssh-keygen -A             # 모든 타입 새로 생성
rm /etc/ssh/ssh_host_dsa_key*    # 약한 알고리즘 제거
```

회전 시: 새 키 추가 → 클라이언트들이 known_hosts 에 추가할 시간 → 옛 키 제거. 또는 호스트 인증서 (13.5) 면 그냥 새 인증서 발급.

## 27.4 fail2ban

```ini
# /etc/fail2ban/jail.local
[sshd]
enabled = true
maxretry = 3
findtime = 10m
bantime = 1h
```

키 인증만 쓰는 환경에선 효용 줄지만, 22 가 인터넷에 노출돼 있으면 로그 노이즈 줄이는 가치는 있다.

## 27.5 포트 변경의 가치

22 → 2222 는 보안 향상이 아니라 **로그 노이즈 감소**다. 자동 스캐너의 99% 가 22 만 본다. 노이즈 줄이려고 옮기는 건 OK, 보안이라고 생각하면 NG.

## 27.6 무중단 sshd 재시작

```bash
systemctl reload sshd      # 기존 세션 안 끊김
```

`restart` 는 기존 세션을 끊는다. 비상 시에만.

## 27.7 limit / namespace

systemd 로 sshd 를 cgroup 제한:

```ini
# /etc/systemd/system/sshd.service.d/limits.conf
[Service]
LimitNOFILE=65536
TasksMax=4096
```

---

# 28장. PAM 과 2FA, FIDO2/U2F

## 28.1 Google Authenticator (TOTP)

```bash
sudo apt install libpam-google-authenticator
google-authenticator    # 사용자별 설정
```

`/etc/pam.d/sshd`:

```
auth required pam_google_authenticator.so nullok
```

`/etc/ssh/sshd_config`:

```
ChallengeResponseAuthentication yes
KbdInteractiveAuthentication yes
UsePAM yes
AuthenticationMethods publickey,keyboard-interactive
```

키 + TOTP 둘 다 통과해야 함.

## 28.2 FIDO2 / U2F

```bash
ssh-keygen -t ed25519-sk -O resident -O verify-required -C "yubikey"
```

키를 만들 때 YubiKey 가 꽂혀 있어야 하고, 사용 시마다 터치 (또는 verify-required 면 PIN+터치). 가장 강한 사용자 인증.

서버는 OpenSSH 8.2 이상이면 별도 설정 없이 받는다.

## 28.3 Duo

```
# /etc/pam.d/sshd
auth required /lib64/security/pam_duo.so
```

```
# sshd_config
ChallengeResponseAuthentication yes
UsePAM yes
AuthenticationMethods publickey,keyboard-interactive
UseDNS no
```

## 28.4 SSO 결합 — Teleport / Boundary / Okta ASA

이들은 결국 13장의 SSH 인증서를 SSO 로 발급해 준다. PAM 보다 운영 편하고 감사 좋다.

---

# 29장. 감사와 로깅

## 29.1 sshd 로그

```
LogLevel VERBOSE
```

이 한 줄로 어느 키가 인증에 쓰였는지(SHA256 핑거프린트)까지 나온다.

```
Accepted publickey for alice from 1.2.3.4 port 5678 ssh2: ED25519 SHA256:abcd...
```

journalctl:

```bash
journalctl -u ssh -f
journalctl -u ssh --since "1 hour ago" | grep Accepted
```

## 29.2 rsyslog → 중앙 수집

```
# /etc/rsyslog.d/30-ssh.conf
auth.* @@logserver.example.com:514
```

또는 fluent-bit, vector, syslog-ng.

## 29.3 세션 녹화 — script

```bash
script -t 2>session.timing -a session.log
```

`scriptreplay` 로 재생.

대규모로는 Teleport 의 session recording 또는 `tlog` 가 표준.

## 29.4 auditd 로 명령어 추적

```bash
sudo apt install auditd
sudo auditctl -a always,exit -F arch=b64 -S execve -k ssh-sessions
```

## 29.5 강제 명령 + 로깅

`force-command="/usr/local/bin/wrap.sh"` 의 wrap.sh 가 입력/출력을 그대로 syslog 에 남기게.

```bash
#!/bin/bash
exec script -q -c "$SSH_ORIGINAL_COMMAND" /var/log/ssh-sessions/$(date +%s)-$USER.log
```

---

# 30장. 보안 강화 (Hardening)

체크리스트:

- [ ] PasswordAuthentication no
- [ ] PermitRootLogin prohibit-password (또는 no)
- [ ] PubkeyAuthentication yes
- [ ] AuthenticationMethods publickey 또는 publickey,keyboard-interactive
- [ ] 약한 알고리즘 제거 (3DES, RC4, CBC, SHA1 MAC)
- [ ] ed25519 호스트 키
- [ ] LogLevel VERBOSE
- [ ] AllowUsers / AllowGroups 화이트리스트
- [ ] MaxAuthTries 3, LoginGraceTime 30
- [ ] X11Forwarding no (필요 없으면)
- [ ] AgentForwarding/TcpForwarding 화이트 호스트만
- [ ] ChrootDirectory + internal-sftp (SFTP 전용 사용자)
- [ ] fail2ban / sshguard
- [ ] firewall (ufw/nftables) 22 는 VPN/허용IP 만
- [ ] SSH CA 로 키 분배 자동화
- [ ] 짧은 인증서 만료 (1-8h)
- [ ] FIDO2 키 의무화 (sk 키 또는 PAM)
- [ ] 로그 → SIEM
- [ ] 호스트 키 / SSHFP DNSSEC
- [ ] 정기적인 `ssh-keygen -e -f host_key | openssl ...` 점검

## 30.1 ssh-audit

```bash
pip install ssh-audit
ssh-audit host
```

각 알고리즘별 점수와 권고. 점수 안 나오면 27.1 의 KexAlgorithms/Ciphers/MACs 를 손본다.

## 30.2 lynis

```bash
sudo lynis audit system
```

SSH 항목이 따로 있다.

---

# 31장. 트러블슈팅 패턴

## 31.1 -v 로 정확히 어디서 실패하나

```bash
ssh -vvv user@host 2>&1 | tee debug.log
```

키 단계 (`Offering public key`), 인증 결과 (`Authentication succeeded`), 채널 (`channel 0: open`) 을 따라간다.

## 31.2 자주 보는 에러

| 메시지 | 원인 |
|---|---|
| Permission denied (publickey) | 서버가 내 키를 거절. authorized_keys, 권한, AllowUsers |
| no matching host key type found | 서버 측 알고리즘 미지원. `-o HostKeyAlgorithms=+ssh-rsa` |
| no matching key exchange method | `-o KexAlgorithms=+...` |
| Too many authentication failures | agent 키가 너무 많음. `IdentitiesOnly yes` |
| Connection closed by ... preauth | 서버가 banner/pre-auth 단계에서 끊음. fail2ban, MaxStartups |
| Host key verification failed | known_hosts 충돌. `ssh-keygen -R` |
| Bad owner or permissions | ~/.ssh 또는 키 파일 권한 |

## 31.3 권한 표준

```
~/.ssh                     700
~/.ssh/authorized_keys     600
~/.ssh/id_*                600
~/.ssh/id_*.pub            644
~/.ssh/config              600
~/.ssh/known_hosts         600
```

홈 디렉토리 자체도 group/other writable 이면 안 됨 (StrictModes).

## 31.4 회사 방화벽 우회 ✓

22 막힘 → `Port 443` 으로 sshd 추가 청취:

```
Port 22
Port 443
```

GitHub 가 `ssh.github.com:443` 을 운영하는 이유.

## 31.5 ConnectionResetByPeer 디버깅

```bash
ssh -o ProxyCommand="nc -v %h %p" host 2>&1 | head
```

TCP 단의 RST 인지, SSH 핸드셰이크 단인지 분리.

## 31.6 MTU 문제

VPN/터널 안에서 패킷이 깨지면 SSH 가 멈춰 보인다.

```bash
ssh -o IPQoS=cs0 user@host
```

또는 인터페이스 MTU 를 낮춘다 (1400 등).

---

# 32장. Bastion 패턴과 Zero Trust

## 32.1 고전 Bastion

```
[Internet] → [Bastion (SSH, MFA, audit)] → [Internal hosts (no public IP)]
```

장점: 단일 진입점. 단점: agent forwarding 의 함정, 키 산재.

## 32.2 ProxyJump + 인증서 = 모던 Bastion

- 사용자는 SSO → 짧은 SSH 인증서
- ProxyJump 로 bastion 통과
- bastion 자체엔 키 안 둠
- 모든 세션 녹화

## 32.3 Zero Trust 흐름

1. SSO + device posture 검증
2. 짧은 인증서 발급 (1h)
3. 인증서가 principal 과 source IP 제약 포함
4. 모든 hop 에서 인증서 검증 + 감사
5. 인증서 만료 = 자동 로그아웃

OpenSSH + 자체 발급기로 구현 가능. Teleport/StrongDM 이 SaaS 로 제공.

## 32.4 Bastion 에 SSH 안 노출하기

- AWS SSM Session Manager (11.4) — 22 안 열어도 됨
- Cloudflare Access for SSH (11.3)
- Tailscale SSH — WireGuard 위에서

이쪽이 점차 표준이 되고 있다.

---

# 33장. 컨테이너 / Kubernetes 와 SSH

## 33.1 컨테이너에 SSH 를 넣지 마라 (대부분의 경우)

`docker exec`, `kubectl exec` 가 본질적으로 같은 일을 한다. SSH 는 운영 표면적만 늘린다.

## 33.2 그래도 필요할 때

- 디버그용 ad-hoc 컨테이너에 sshd
- legacy 앱이 SSH 를 인터페이스로 가짐 (Git, SFTP)

## 33.3 dropbear — 작은 sshd

Alpine 등 슬림 이미지에 자주.

```dockerfile
RUN apk add --no-cache dropbear openssh-keygen \
 && mkdir -p /etc/dropbear \
 && dropbearkey -t ed25519 -f /etc/dropbear/dropbear_ed25519_host_key
CMD ["/usr/sbin/dropbear", "-F", "-E", "-w", "-g"]
```

## 33.4 kubectl 과 SSH

```bash
kubectl port-forward svc/myapp 8080:80
```

이게 사실상 `-L` 의 k8s 버전이다.

```bash
kubectl exec -it pod-name -- /bin/bash
```

이건 `ssh` 의 k8s 버전. SSH 안 깔아도 됨.

## 33.5 SSH 로 k8s API 터널링

bastion 만 클러스터 네트워크에 있을 때:

```bash
ssh -L 6443:kubernetes.default.svc:6443 user@bastion
kubectl --server=https://127.0.0.1:6443 ...
```

## 33.6 git-sync / image registry over SSH

오프라인 클러스터에 image / git 데이터를 넣을 때 reverse tunnel 활용 (8.2).

---

# 34장. 종합 시나리오 워크북

이 장은 실전 시나리오 하나하나를 처음부터 끝까지 따라간다.

## 시나리오 1 — 카페 와이파이에서 안전한 브라우징

목표: 노트북의 모든 트래픽을 집의 데스크탑(또는 VPS)을 거쳐서 내보내기.

```bash
# 1) 한 번
ssh-copy-id me@home.example.com

# 2) 동적 프록시
ssh -fND 1080 me@home.example.com

# 3) 시스템 프록시 또는 브라우저: SOCKS5 127.0.0.1:1080
```

DNS 누설 막기 — 브라우저 설정 또는 `--socks5-hostname`. 끝.

## 시나리오 2 — 회사 DB 에 노트북에서 접속

방화벽 정책: `bastion.corp.com` 만 22 가 열려 있다. DB 는 `db.internal:5432`.

`~/.ssh/config`:

```ssh
Host bastion
    HostName bastion.corp.com
    User myname
    IdentityFile ~/.ssh/id_corp
    IdentitiesOnly yes

Host db-tunnel
    HostName db.internal
    User myname
    ProxyJump bastion
    LocalForward 5432 db.internal:5432
    ExitOnForwardFailure yes
```

```bash
ssh -fN db-tunnel
psql -h 127.0.0.1 -U app mydb
```

## 시나리오 3 — 자택 PC 에 외출에서 접속

가정: VPS 에 24시간 SSH 띄움. 자택 PC 가 NAT 뒤.

자택 PC `/etc/systemd/system/home-tunnel.service`:

```ini
[Unit]
Description=reverse tunnel to vps
After=network-online.target

[Service]
Restart=always
ExecStart=/usr/bin/autossh -M 0 -N \
    -o ServerAliveInterval=30 -o ServerAliveCountMax=3 \
    -o ExitOnForwardFailure=yes \
    -i /home/me/.ssh/id_tunnel \
    -R 127.0.0.1:2222:localhost:22 me@vps.example.com

[Install]
WantedBy=multi-user.target
```

VPS 의 sshd_config: `GatewayPorts clientspecified` (필요 시).

외부에서:

```bash
ssh -p 2222 -o ProxyJump=me@vps.example.com me@127.0.0.1
# 또는 config 에 박기
```

config:

```ssh
Host home
    HostName 127.0.0.1
    Port 2222
    User me
    ProxyJump me@vps.example.com
```

`ssh home` → vps 거쳐 자택 PC.

## 시나리오 4 — 친구에게 내 데모 서버 보여주기

```bash
# 로컬에서 8080 으로 데모 실행
ssh -fNR 8080:localhost:8080 me@vps.example.com
```

VPS 에 nginx 로 reverse proxy:

```nginx
server {
    listen 80;
    server_name demo.example.com;
    location / { proxy_pass http://127.0.0.1:8080; }
}
```

친구는 `http://demo.example.com`. 끝.

## 시나리오 5 — kubectl 을 회사 클러스터에

```ssh
Host k8s-tunnel
    HostName api.k8s.corp
    User me
    ProxyJump bastion
    LocalForward 6443 api.k8s.corp:6443
    ExitOnForwardFailure yes
```

```bash
ssh -fN k8s-tunnel
KUBECONFIG=~/work/kubeconfig kubectl --server=https://127.0.0.1:6443 get pods -A
```

## 시나리오 6 — 대량 호스트에 동시 패치

```bash
cat hosts.txt | parallel -j 50 \
    ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=accept-new \
        ubuntu@{} "sudo apt-get update && sudo apt-get -y upgrade"
```

ControlMaster + pipelining 이면 더 빠르다. Ansible 이 결국 같은 일을 더 잘한다.

## 시나리오 7 — Git 서버를 ssh 로만

서버에 `git` 사용자, `git-shell`:

```bash
sudo adduser --disabled-password git
sudo chsh -s /usr/bin/git-shell git
sudo -u git mkdir -p ~git/.ssh ~git/repos/myrepo.git
sudo -u git git --git-dir=~git/repos/myrepo.git init --bare
```

`~git/.ssh/authorized_keys`:

```
restrict,command="git-shell -c '$SSH_ORIGINAL_COMMAND'" ssh-ed25519 AAAA... dev1
```

```bash
git clone git@host:repos/myrepo.git
```

## 시나리오 8 — SSH CA 로 사내 키 분배 끝내기

```bash
# 1) 한 번 — CA
ssh-keygen -t ed25519 -f user_ca -C user-ca -N ''
ssh-keygen -t ed25519 -f host_ca -C host-ca -N ''

# 2) 모든 서버 — 사용자 CA 신뢰
sudo cp user_ca.pub /etc/ssh/user_ca.pub
echo "TrustedUserCAKeys /etc/ssh/user_ca.pub" | sudo tee -a /etc/ssh/sshd_config
sudo systemctl reload ssh

# 3) 모든 서버 — 호스트 인증서
ssh-keygen -s host_ca -I "$(hostname)" -n "$(hostname),$(hostname -I | tr ' ' ',')" -V +52w -h /etc/ssh/ssh_host_ed25519_key.pub
sudo mv /etc/ssh/ssh_host_ed25519_key-cert.pub /etc/ssh/
echo "HostCertificate /etc/ssh/ssh_host_ed25519_key-cert.pub" | sudo tee -a /etc/ssh/sshd_config
sudo systemctl reload ssh

# 4) 모든 사용자 — 호스트 CA 신뢰
echo "@cert-authority *.example.com,10.0.0.* $(cat host_ca.pub)" >> ~/.ssh/known_hosts

# 5) 매일 — 사용자 인증서
ssh-keygen -s user_ca -I "alice@$(date +%F)" -n alice -V +24h ~alice/.ssh/id_ed25519.pub
```

이 다섯 단계가 끝나면 새 서버에 누구의 키도 따로 안 넣는다. 사용자 키도 매일 자동 발급.

## 시나리오 9 — 쿠버네티스 서비스 + DB 한꺼번에 노출

```ssh
Host dev-tunnels
    HostName bastion.dev
    User me
    LocalForward 5432 postgres.dev.svc:5432
    LocalForward 6379 redis.dev.svc:6379
    LocalForward 9200 elastic.dev.svc:9200
    LocalForward 9090 prom.dev.svc:9090
    LocalForward 3000 grafana.dev.svc:3000
    DynamicForward 1080
    ServerAliveInterval 30
    ExitOnForwardFailure yes
```

```bash
ssh -fN dev-tunnels
```

이 한 줄이 곧 dev 환경 전체.

## 시나리오 10 — 점프 + tmux + 자동 재접속

```ssh
Host prod
    HostName prod.example.com
    User app
    ProxyJump bastion
    RequestTTY yes
    RemoteCommand tmux new -A -s main
    ServerAliveInterval 30
    ServerAliveCountMax 3
```

`ssh prod` → bastion 통과 → prod 에서 tmux session main 자동 attach. 인터넷 끊어도 다음 ssh 로 그대로 들어옴.

mosh 와 결합:

```bash
mosh --ssh="ssh -J bastion" prod -- tmux new -A -s main
```

세션이 절대 안 끊긴다.

## 시나리오 11 — 클라우드 메타데이터에서 호스트 키 가져와 known_hosts 채우기

AWS:

```bash
aws ec2 get-console-output --instance-id i-abc \
  | sed -n '/BEGIN SSH HOST KEY KEYS/,/END SSH HOST KEY KEYS/p' \
  | grep '^ssh-' \
  | awk -v h=$IP '{print h" "$0}' >> ~/.ssh/known_hosts
```

`StrictHostKeyChecking yes` 로 두고 처음 접속해도 안전.

## 시나리오 12 — 폐쇄망 서버에 임시로 인터넷 주기

폐쇄망 서버의 패키지 업데이트가 필요한데 인터넷이 없을 때. 내 노트북엔 인터넷 있음.

서버에서:

```bash
ssh -R 1080 me@laptop
```

(여기서 -R 에 호스트:포트 안 주고 포트만 → 동적 SOCKS 의 reverse 버전)

서버 안:

```bash
http_proxy=socks5h://127.0.0.1:1080 \
https_proxy=socks5h://127.0.0.1:1080 \
sudo -E apt-get update
```

내 노트북이 인터넷 게이트웨이가 된다.

## 시나리오 13 — SSH 만으로 DNS over SSH

회사가 DNS 강제 + 검열. 일시 우회:

```bash
ssh -L 5354:1.1.1.1:53 user@vps     # TCP DNS 만 됨
```

```bash
dig @127.0.0.1 -p 5354 +tcp blocked.example.com
```

체계적으론 DoH/DoT 가 정답. SSH 는 빠른 임시방편.

## 시나리오 14 — 초저속 회선에서 SSH

```bash
ssh -C \
    -o "Ciphers=aes128-gcm@openssh.com" \
    -o "MACs=umac-64-etm@openssh.com" \
    -o "Compression=yes" \
    -o "TCPKeepAlive=yes" \
    user@host
```

mosh 가 나은 경우가 많다.

## 시나리오 15 — 완전한 ssh config 템플릿

```ssh
# ─── 글로벌 ──────────────────────────────────────────────
Host *
    AddKeysToAgent yes
    IdentitiesOnly yes
    HashKnownHosts yes
    StrictHostKeyChecking accept-new
    ServerAliveInterval 60
    ServerAliveCountMax 3
    ControlMaster auto
    ControlPath ~/.ssh/cm-%C
    ControlPersist 10m

# ─── 회사 ────────────────────────────────────────────────
Host bastion
    HostName bastion.corp.com
    User me
    Port 22
    IdentityFile ~/.ssh/id_corp
    ForwardAgent no

Host *.corp.internal
    User me
    IdentityFile ~/.ssh/id_corp
    ProxyJump bastion

# ─── 클라우드 ────────────────────────────────────────────
Host i-* mi-*
    User ec2-user
    IdentityFile ~/.ssh/id_aws
    ProxyCommand sh -c "aws ssm start-session --target %h \
        --document-name AWS-StartSSHSession --parameters portNumber=%p"

# ─── 개인 ────────────────────────────────────────────────
Host home
    HostName home.dyn.example.com
    User me
    Port 2222
    IdentityFile ~/.ssh/id_personal
    LocalForward 8080 192.168.1.10:80

Host vps
    HostName vps.example.com
    User root
    IdentityFile ~/.ssh/id_personal

# ─── Git ─────────────────────────────────────────────────
Host github.com
    User git
    IdentityFile ~/.ssh/id_personal_gh
    IdentitiesOnly yes

Host github-work
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_work_gh
    IdentitiesOnly yes

# ─── Tor ─────────────────────────────────────────────────
Host *.onion
    ProxyCommand nc -X 5 -x 127.0.0.1:9050 %h %p
    User onion
```

이 한 파일이 일주일치 삽질을 절약한다.

## 시나리오 16 — 회사 HTTP CONNECT 프록시 통과해서 외부 SSH

회사가 모든 아웃바운드를 HTTP 프록시로만 강제. 22 직접 안 됨.

```bash
sudo apt install corkscrew
```

`~/.ssh/config`:

```ssh
Host github.com gitlab.com bitbucket.org
    User git
    Port 443
    HostName ssh.%h           # github 의 ssh.github.com:443 처럼
    ProxyCommand corkscrew proxy.corp 8080 %h %p

Host my-vps
    HostName vps.example.com
    User me
    Port 443                  # vps 에 sshd 가 443 도 청취
    ProxyCommand corkscrew proxy.corp 8080 %h %p
```

VPS 의 `/etc/ssh/sshd_config`:

```
Port 22
Port 443
```

이제 회사 안에서 git push, my-vps 접속 모두 정상.

`corkscrew` 가 없으면 `nc -X connect -x proxy.corp:8080 %h %p` 로 대체.

## 시나리오 17 — VPS 를 통한 양방향 chained tunnel

내가 집에서 회사 내부 서버에 가야 하고, 회사 안에서 내 집 NAS 에도 가야 한다. VPS 를 만남의 광장으로.

집 노트북 → VPS:

```bash
ssh -fN -L 9000:localhost:9000 -R 9001:nas.lan:445 me@vps
```

회사 PC → VPS:

```bash
ssh -fN -R 9002:internal.corp:443 -L 9003:localhost:9001 me@vps
```

VPS 위에서 두 reverse 가 만나 서로 연결되는 형태로 socat 또는 nginx stream 으로 다리 놓기:

```bash
# vps 에서
socat TCP-LISTEN:9000,reuseaddr,fork TCP:localhost:9002 &  # 집 → 회사
socat TCP-LISTEN:9003,reuseaddr,fork TCP:localhost:9001 &  # 회사 → 집
```

이제 집에서 `https://localhost:9000` = 회사 internal.corp:443.
회사에서 `smb://localhost:9003` = 집 NAS.

## 시나리오 18 — 멀티홉 -L 체이닝

`A → B → C → D` 의 D 의 8080 을 A 의 8080 으로:

A `~/.ssh/config`:

```ssh
Host D-via
    HostName D
    User app
    ProxyJump B,C
    LocalForward 8080 localhost:8080
```

```bash
ssh -fN D-via
curl http://localhost:8080
```

ProxyJump 가 다단계라도 LocalForward 의 끝점은 *D 가 본* localhost. 한 줄로 끝.

## 시나리오 19 — DB replication 터널

마스터(corp) → DR 사이트 슬레이브(dr) 로 PostgreSQL replication. 둘 다 SSH 만 가능.

DR 측에서:

```bash
ssh -fN -L 5432:localhost:5432 replicator@master.corp
```

`recovery.conf` 또는 `primary_conninfo`:

```
primary_conninfo = 'host=127.0.0.1 port=5432 user=repl password=...'
```

WAL 스트림이 SSH 채널로 흘러 모든 트래픽 암호화.

영구화는 systemd unit + autossh (8.7).

## 시나리오 20 — SMB / NFS 를 SSH 로

원격 NAS 의 SMB 공유를 안전하게 마운트.

```bash
ssh -fN -L 4445:nas.internal:445 me@bastion
sudo mount -t cifs //127.0.0.1/share /mnt/nas \
    -o port=4445,user=me,vers=3.0
```

NFS 는 RPC portmapper 때문에 까다롭다. NFSv4 + 단일 포트(2049) 면 같은 패턴:

```bash
ssh -fN -L 2049:nfs.internal:2049 me@bastion
sudo mount -t nfs4 -o port=2049 127.0.0.1:/export /mnt/nfs
```

NFSv3 면 sshuttle (17장) 또는 stunnel + NFSv4.

## 시나리오 21 — 원격 프린터를 SSH 로

집 프린터 (IPP 631) 를 외출 노트북에서:

```bash
ssh -fN -L 6631:printer.lan:631 me@home-vps
```

CUPS 에 추가:

```
ipp://127.0.0.1:6631/printers/HP_LaserJet
```

## 시나리오 22 — VNC over SSH

원격 데스크탑을 안전하게.

원격에서 (한 번):

```bash
sudo apt install tigervnc-standalone-server
vncpasswd
vncserver -localhost yes :1     # 5901 만 127.0.0.1 에 청취
```

내 쪽:

```bash
ssh -fN -L 5901:localhost:5901 me@host
vncviewer 127.0.0.1::5901
```

`-localhost yes` 가 핵심. 외부 5901 노출 0.

## 시나리오 23 — RDP over SSH

윈도우 RDP 를 SSH 너머로:

```bash
ssh -fN -L 3389:windows.internal:3389 me@bastion
xfreerdp /v:127.0.0.1 /u:user /size:1920x1080
```

윈도우의 RDP NLA 와 SSH 의 인증이 이중으로 걸린다.

## 시나리오 24 — Jupyter / VS Code Remote / TensorBoard

GPU 서버에 노트북 띄우고 로컬 브라우저로:

```bash
ssh -L 8888:localhost:8888 -L 6006:localhost:6006 gpu-host
gpu-host$ jupyter lab --no-browser --port=8888
gpu-host$ tensorboard --logdir runs --port 6006 --host 127.0.0.1
```

브라우저: `http://localhost:8888`, `http://localhost:6006`. 토큰은 jupyter 가 출력한 그것.

VS Code 의 Remote-SSH 확장은 사실 위 메커니즘을 자동화한 것이다. config 에 ProxyJump 만 잘 두면 그대로 동작.

## 시나리오 25 — 로컬 개발 + 원격 마이크로서비스

마이크로서비스 30개를 노트북에 다 못 띄움. dev 클러스터의 dependency 만 끌어옴.

```ssh
Host dev-deps
    HostName dev.bastion.corp
    User me
    LocalForward 5432  postgres.dev.svc:5432
    LocalForward 6379  redis.dev.svc:6379
    LocalForward 9092  kafka.dev.svc:9092
    LocalForward 8500  consul.dev.svc:8500
    LocalForward 4222  nats.dev.svc:4222
    LocalForward 9200  elastic.dev.svc:9200
    LocalForward 9000  minio.dev.svc:9000
    DynamicForward 1080
    ServerAliveInterval 30
    ExitOnForwardFailure yes
```

```bash
ssh -fN dev-deps
DATABASE_URL=postgres://app@127.0.0.1/dev \
REDIS_URL=redis://127.0.0.1 \
KAFKA_BROKER=127.0.0.1:9092 \
go run ./cmd/myservice
```

내 한 서비스만 로컬에서 디버깅, 나머지는 dev 클러스터 진짜.

## 시나리오 26 — Webhook 수신을 reverse tunnel 로 (ngrok 대체)

GitHub/Slack 이 내 노트북의 8080 으로 webhook 을 보내야 하는데 NAT 뒤다.

VPS 의 nginx:

```nginx
server {
    listen 443 ssl http2;
    server_name hook.example.com;
    ssl_certificate /etc/letsencrypt/live/hook.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/hook.example.com/privkey.pem;
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }
}
```

노트북:

```bash
ssh -fNR 8080:localhost:8080 me@vps
```

GitHub webhook URL: `https://hook.example.com/`. 직접 만든 ngrok.

## 시나리오 27 — 시간 제한 데모 터널

`expiry-time` 인증서 + autossh:

```bash
ssh-keygen -s user_ca -I "demo-2026-05-08" -n demo \
    -V +2h \
    -O force-command="echo 'demo only'" \
    demo.pub

# 데모 시작
autossh -fNR 8080:localhost:8080 -i demo-cert demo@vps
# 2시간 후 인증서 만료 → 자동 끊김
```

발 디딘 자국 안 남기는 게 핵심.

## 시나리오 28 — 동작 중인 SSH 에 포워딩 동적으로 추가

`~C` 를 외워두면 신세계.

```
me@host:~$ <ENTER>~C
ssh> -L 9090:internal:9090
Forwarding port.

me@host:~$ <ENTER>~C
ssh> -KR 8080
Canceled forwarding.
```

또는 ControlMaster 면 다른 터미널에서:

```bash
ssh -O forward -L 9090:internal:9090 host
ssh -O cancel  -L 9090:internal:9090 host
```

세션 안 끊고 포트만 바꿔 가며 작업.

## 시나리오 29 — IPv6 전용 호스트에 IPv4 노트북에서

```ssh
Host v6-only
    HostName 2001:db8::42
    AddressFamily inet6
    ProxyJump dual-stack-bastion
```

```bash
ssh v6-only
```

bastion 만 dual stack 이면 끝.

## 시나리오 30 — 노트북에 Wake-on-LAN 후 SSH

VPS → 자택 라우터 (reverse tunnel) → WOL 매직 패킷 → PC → SSH.

자택 라우터에 reverse tunnel:

```bash
autossh -fNR 22022:localhost:22 me@vps
```

원격에서:

```bash
ssh -p 22022 -o ProxyJump=me@vps me@127.0.0.1 \
    "wakeonlan AA:BB:CC:DD:EE:FF"
sleep 60
ssh -J me@vps me@home-pc
```

config:

```ssh
Host home-pc
    HostName 192.168.1.10
    User me
    ProxyJump router-via-vps
    LocalCommand ssh router-via-vps "wakeonlan AA:BB:CC:DD:EE:FF" && sleep 60
    PermitLocalCommand yes
```

`ssh home-pc` → 라우터에 WOL 시키고 → 깨어나면 들어감.

## 시나리오 31 — 폐쇄망 Docker registry 동기화

dev 의 registry:5000 → prod 의 registry:5000 (둘 다 직접 인터넷 안 됨).

중간 노트북:

```bash
# 두 터널 동시
ssh -fN -L 5000:dev-registry:5000 dev-bastion
ssh -fN -L 5001:prod-registry:5000 prod-bastion

# 노트북에서 동기화
docker pull 127.0.0.1:5000/myapp:1.2.3
docker tag  127.0.0.1:5000/myapp:1.2.3 127.0.0.1:5001/myapp:1.2.3
docker push 127.0.0.1:5001/myapp:1.2.3
```

`skopeo copy --src-tls-verify=false --dest-tls-verify=false ...` 가 더 빠르고 깔끔.

## 시나리오 32 — Mosquitto / MQTT 브로커 over SSH

IoT 게이트웨이의 MQTT 1883/8883 을 안전하게 모니터링:

```bash
ssh -fN -L 1883:mqtt.factory:1883 ops@gateway
mosquitto_sub -h 127.0.0.1 -t '#' -v
```

장비 펌웨어가 평문 1883 만 지원해도 SSH 가 외부 구간을 보호.

## 시나리오 33 — Kafka multi-broker 터널

Kafka 클라이언트는 리스 한 broker 뿐 아니라 *advertised.listeners* 의 각 broker 에 다 붙는다. 단일 -L 로는 안 됨.

각 broker 별로 -L 하고 + advertised.listeners 를 127.0.0.1 의 매핑 주소로 설정:

```bash
ssh -fN \
    -L 19092:b1.kafka:9092 \
    -L 19093:b2.kafka:9092 \
    -L 19094:b3.kafka:9092 \
    bastion
```

또는 sshuttle 한 번이면 끝:

```bash
sshuttle -r bastion 10.0.0.0/24 --dns
```

이게 9 잡 필요할 때 -L 의 한계다.

## 시나리오 34 — Jenkins agent 를 reverse tunnel 로

Jenkins master 가 외부, agent 가 내부. agent 에서 master 로 outbound 만 가능.

agent 가 master 로:

```bash
ssh -fNR 50000:localhost:50000 jenkins@master
```

master 가 jnlp 50000 을 127.0.0.1 으로만 청취. agent 가 reverse tunnel 통해 자기 자신에게 jnlp 연결처럼 보이게.

## 시나리오 35 — 2단계 reverse tunnel

내 PC → A → B 로 거꾸로 닿게 하고 싶음 (A 와 B 는 NAT 안에 있고 서로 못 봄, 둘 다 내 PC 로 outbound 만 가능).

A 가:

```bash
ssh -fNR 22001:localhost:22 me@my-pc
```

B 가:

```bash
ssh -fNR 22002:localhost:22 me@my-pc
```

내 PC 에서:

```bash
ssh -p 22001 a-user@127.0.0.1
ssh -p 22002 b-user@127.0.0.1
```

A → B 는 내 PC 를 거치는 chain 으로:

```bash
ssh -L 9999:127.0.0.1:22002 -p 22001 a-user@127.0.0.1
# 그 위에서
ssh -p 9999 b-user@127.0.0.1
```

## 시나리오 36 — 라이브 마이그레이션 (KVM/libvirt)

호스트 A 의 VM 을 호스트 B 로 옮기는데 둘 사이 직통 안 됨. SSH 로 우회:

```bash
virsh -c qemu+ssh://root@A/system migrate \
    --live --persistent --undefinesource \
    myvm qemu+ssh://root@B/system
```

libvirt 가 알아서 SSH 채널을 통해 메모리/디스크 동기화. 보안과 우회를 한 번에.

## 시나리오 37 — Step-up 인증으로 짧은 터널

YubiKey 터치 = 2시간 터널.

```bash
ssh-keygen -t ed25519-sk -O verify-required -f ~/.ssh/id_demo

# 터치 → 매번 확인
ssh -fN \
    -i ~/.ssh/id_demo \
    -o IdentitiesOnly=yes \
    -L 5432:db:5432 bastion
```

ControlPersist 0 으로 두면 매 명령마다 터치. 너무 빡세면 2h.

## 시나리오 38 — 컨테이너 sidecar 로 SSH 터널

쿠버네티스 파드 안의 어떤 앱이 외부 DB 에 SSH 터널로 가야 함. 앱은 모르고 환경변수만 본다.

```yaml
apiVersion: v1
kind: Pod
spec:
  containers:
    - name: app
      image: myapp
      env:
        - name: DATABASE_URL
          value: postgres://app@127.0.0.1:5432/prod
    - name: ssh-tunnel
      image: kroniak/ssh-client
      command: ["sh","-c"]
      args:
        - |
          mkdir -p ~/.ssh
          echo "$SSH_KEY" > ~/.ssh/id && chmod 600 ~/.ssh/id
          echo "$KNOWN" > ~/.ssh/known_hosts
          exec ssh -N -i ~/.ssh/id \
            -o ExitOnForwardFailure=yes \
            -o ServerAliveInterval=30 \
            -L 0.0.0.0:5432:db.corp:5432 \
            tunnel@bastion.corp
      env:
        - { name: SSH_KEY, valueFrom: { secretKeyRef: { name: ssh, key: id }}}
        - { name: KNOWN,   valueFrom: { configMapKeyRef: { name: ssh, key: known }}}
```

파드의 두 컨테이너는 같은 네트워크 namespace → app 의 127.0.0.1:5432 = 사이드카의 -L. 앱 코드 수정 0.

## 시나리오 39 — 사이트 to 사이트 SSH-VPN

두 사무실을 영구 연결. WireGuard 가 진짜 답이지만 SSH 만 허용되는 환경에선:

A 게이트웨이:

```bash
sudo ssh -fN -w 0:0 \
    -o "ServerAliveInterval=30" \
    -o "Tunnel=point-to-point" \
    root@b-gateway

sudo ip addr add 10.99.0.1/30 peer 10.99.0.2 dev tun0
sudo ip link set tun0 up
sudo ip route add 192.168.20.0/24 via 10.99.0.2 dev tun0
```

B 게이트웨이 (sshd 의 PermitRootLogin + PermitTunnel + post-login script):

```bash
# /root/.ssh/authorized_keys
tunnel,command="/usr/local/bin/setup-tun.sh" ssh-ed25519 AAAA... a-gateway
```

```bash
# /usr/local/bin/setup-tun.sh
ip addr add 10.99.0.2/30 peer 10.99.0.1 dev tun0
ip link set tun0 up
ip route add 192.168.10.0/24 via 10.99.0.1 dev tun0
sleep 86400
```

성능은 나쁘지만 "전용선이 SSH 만 허용" 같은 이상한 환경에서 산다.

## 시나리오 40 — 자동 페일오버 터널

두 bastion 이 있고 하나가 죽어도 끊기면 안 됨.

`~/.ssh/config`:

```ssh
Host primary
    HostName b1.corp
    User me

Host secondary
    HostName b2.corp
    User me

Host db-tunnel
    HostName db.corp
    User me
    ProxyCommand sh -c "ssh -W %h:%p primary || ssh -W %h:%p secondary"
    LocalForward 5432 db.corp:5432
```

primary 다운 → secondary 자동. 더 정교하면 `mux` 또는 keepalived.

---

# 부록 A. 알고리즘과 암호 스위트

## A.1 키 교환 (Kex)

| 알고리즘 | 권장 |
|---|---|
| curve25519-sha256 | ★★★★★ |
| curve25519-sha256@libssh.org | ★★★★★ (별칭) |
| sntrup761x25519-sha512@openssh.com | ★★★★★ (post-quantum hybrid, OpenSSH 9+) |
| diffie-hellman-group16-sha512 | ★★★ |
| diffie-hellman-group18-sha512 | ★★★★ |
| ecdh-sha2-nistp256/384/521 | ★★ |
| diffie-hellman-group1-sha1 | ✗ |
| diffie-hellman-group14-sha1 | ✗ |

## A.2 대칭암호 (Cipher)

| 알고리즘 | 권장 |
|---|---|
| chacha20-poly1305@openssh.com | ★★★★★ |
| aes256-gcm@openssh.com | ★★★★★ |
| aes128-gcm@openssh.com | ★★★★ |
| aes256-ctr | ★★★ |
| aes128-ctr | ★★★ |
| 3des-cbc | ✗ |
| arcfour* | ✗ |
| *-cbc | ✗ |

## A.3 MAC

| 알고리즘 | 권장 |
|---|---|
| hmac-sha2-512-etm@openssh.com | ★★★★★ |
| hmac-sha2-256-etm@openssh.com | ★★★★★ |
| umac-128-etm@openssh.com | ★★★★ |
| hmac-sha1 | ✗ |

ETM (Encrypt-then-MAC) 이 아닌 MAC 은 피한다.

## A.4 호스트 키 / 사용자 키 알고리즘

| 알고리즘 | 권장 |
|---|---|
| ssh-ed25519 | ★★★★★ |
| ssh-ed25519-cert-v01@openssh.com | ★★★★★ (인증서) |
| sk-ssh-ed25519@openssh.com | ★★★★★ (FIDO2) |
| rsa-sha2-512 / rsa-sha2-256 | ★★★ |
| ssh-rsa (SHA1) | ✗ |
| ssh-dss | ✗ |

## A.5 검사 명령

```bash
ssh -Q kex
ssh -Q cipher
ssh -Q mac
ssh -Q HostKeyAlgorithms

nmap --script ssh2-enum-algos -p 22 host
ssh-audit host
```

---

# 부록 B. 주요 옵션 레퍼런스

## B.1 ssh 명령행 옵션

| 옵션 | 의미 |
|---|---|
| `-A` | agent forwarding |
| `-a` | agent forwarding 비활성 |
| `-C` | 압축 |
| `-D port` | 동적 포트포워딩 (SOCKS) |
| `-E file` | 디버그 로그를 파일로 |
| `-e char` | escape 문자 변경 |
| `-F file` | 다른 config |
| `-f` | 인증 후 백그라운드 |
| `-G` | config 덤프 |
| `-g` | GatewayPorts |
| `-i file` | identity file |
| `-J host` | ProxyJump |
| `-K` | GSSAPI delegated credentials |
| `-k` | GSSAPI no delegate |
| `-L l:h:p` | 로컬 포워딩 |
| `-l user` | 사용자 |
| `-M` | ControlMaster 마스터 |
| `-N` | 명령 없음 |
| `-n` | stdin /dev/null |
| `-O cmd` | ControlMaster 제어 |
| `-o opt` | 옵션 |
| `-p port` | 포트 |
| `-Q feat` | 지원 알고리즘 질의 |
| `-q` | quiet |
| `-R r:h:p` | 원격 포워딩 |
| `-S sock` | ControlPath |
| `-T` | TTY 비할당 |
| `-t` | TTY 강제 |
| `-V` | 버전 |
| `-v/-vv/-vvv` | 디버그 |
| `-W h:p` | stdin/stdout 포워딩 |
| `-w l:r` | tun/tap 디바이스 |
| `-X` | X11 |
| `-x` | X11 끄기 |
| `-Y` | trusted X11 |
| `-y` | syslog |

## B.2 자주 쓰는 -o 옵션

```
ConnectTimeout=5
ConnectionAttempts=3
ServerAliveInterval=60
ServerAliveCountMax=3
TCPKeepAlive=yes
StrictHostKeyChecking={yes|no|ask|accept-new|off}
UserKnownHostsFile=~/.ssh/known_hosts
HashKnownHosts=yes
IdentityFile=~/.ssh/id_x
IdentitiesOnly=yes
PreferredAuthentications=publickey,keyboard-interactive
PubkeyAuthentication=yes
PasswordAuthentication=no
KbdInteractiveAuthentication=no
BatchMode=yes
ForwardAgent=no
ForwardX11=no
ForwardX11Trusted=no
RequestTTY={no|yes|force|auto}
RemoteCommand=tmux new -A -s main
PermitLocalCommand=yes
LocalCommand=...
ProxyJump=...
ProxyCommand=...
ControlMaster={no|yes|ask|auto|autoask}
ControlPath=...
ControlPersist=10m
ExitOnForwardFailure=yes
LogLevel={QUIET|FATAL|ERROR|INFO|VERBOSE|DEBUG|DEBUG1..3}
LocalForward=5432 db:5432
RemoteForward=2222 localhost:22
DynamicForward=1080
GatewayPorts={no|yes|clientspecified}
Compression={yes|no}
Ciphers=...
KexAlgorithms=...
MACs=...
HostKeyAlgorithms=...
PubkeyAcceptedAlgorithms=...
CertificateFile=~/.ssh/id-cert.pub
SendEnv=LANG LC_*
SetEnv=FOO=bar
TunnelDevice=any:any
Tunnel={no|point-to-point|ethernet|yes}
VerifyHostKeyDNS={no|yes|ask}
VisualHostKey=yes
AddressFamily={any|inet|inet6}
BindAddress=...
BindInterface=...
EscapeChar=~
ClearAllForwardings=yes
```

## B.3 sshd_config 옵션 (핵심)

```
Port
ListenAddress
HostKey
HostCertificate
TrustedUserCAKeys
RevokedKeys
PermitRootLogin {yes|no|prohibit-password|forced-commands-only}
PubkeyAuthentication
PasswordAuthentication
KbdInteractiveAuthentication
ChallengeResponseAuthentication
UsePAM
AuthenticationMethods publickey,keyboard-interactive
MaxAuthTries
MaxSessions
MaxStartups 10:30:100
LoginGraceTime
ClientAliveInterval
ClientAliveCountMax
TCPKeepAlive
AllowUsers / DenyUsers
AllowGroups / DenyGroups
PermitEmptyPasswords
StrictModes
PrintMotd
Banner
LogLevel VERBOSE
SyslogFacility AUTH
X11Forwarding
X11UseLocalhost
AllowTcpForwarding {yes|no|local|remote|all}
AllowStreamLocalForwarding
GatewayPorts {no|yes|clientspecified}
PermitTunnel {no|yes|point-to-point|ethernet}
PermitOpen
PermitListen
ChrootDirectory
ForceCommand
Subsystem sftp internal-sftp
Match {User|Group|Host|Address|LocalAddress|LocalPort|RDomain|...}
```

---

# 부록 C. 에러 메시지 사전

## C.1 클라이언트 측

### `Permission denied (publickey).`
- 서버가 내 키를 거절. `ssh -vvv` 로 어떤 키를 시도했고 어떻게 답했는지 확인.
- 가능 원인: authorized_keys 누락, 권한 (700/600), AllowUsers/AllowGroups, force-command 거절, IdentitiesOnly 안 켜서 다른 키부터 시도하다가 MaxAuthTries 초과.

### `Permission denied (publickey,gssapi-keyex,gssapi-with-mic).`
- 서버가 비밀번호 비활성. publickey 만 가능. 위와 동일.

### `Too many authentication failures`
- agent 에 키가 너무 많고 IdentitiesOnly 미설정. config 에 `IdentitiesOnly yes` + 명시적 `IdentityFile`.

### `Host key verification failed.`
- known_hosts 와 다름. 진짜 변조면 위험. 정상 변경이면 `ssh-keygen -R hostname`.

### `no matching host key type found. Their offer: ssh-rsa`
- 클라이언트가 SHA1 RSA 거절. 일회성: `-o HostKeyAlgorithms=+ssh-rsa -o PubkeyAcceptedAlgorithms=+ssh-rsa`. 가능하면 서버에 ed25519 키 만들기.

### `kex_exchange_identification: read: Connection reset by peer`
- 방화벽/IDS 가 끊음. fail2ban, MaxStartups, 또는 ISP 의 22 차단. 22 → 443.

### `Connection closed by ... port 22`
- pre-auth 단계. 서버 로그에 단서. 보통 알고리즘 협상 실패.

### `bad permissions: ignore key: /home/x/.ssh/id_x`
- 600 미만으로 권한 풀려있음. `chmod 600`.

### `sign_and_send_pubkey: signing failed for ED25519 ... agent refused operation`
- ssh-add -c 또는 1Password 가 사용자 확인 대기 중. 터치/PIN/허용.

### `Could not resolve hostname`
- DNS. `getent hosts host`. ProxyJump 안에 있으면 *원격이 본* DNS 가 문제.

### `channel 0: open failed: administratively prohibited: open failed`
- 서버가 PermitOpen 으로 막음. -L 의 목적지 변경.

### `mux_client_request_session: read from master failed: Broken pipe`
- ControlMaster 마스터가 죽었거나 stale 한 socket. `ssh -O exit host` 후 재시도.

## C.2 서버 측

### `userauth_pubkey: key type ssh-rsa not in PubkeyAcceptedAlgorithms`
- 클라이언트가 SHA1 RSA 보냄. 서버가 거절. `PubkeyAcceptedAlgorithms +ssh-rsa` (임시) 또는 키 교체.

### `Authentication refused: bad ownership or modes for directory /home/x`
- 홈 디렉토리가 group/other writable. `chmod g-w,o-w ~`.

### `error: AuthorizedKeysCommand failed`
- LDAP/AD 등 외부 키 소스. 별도 디버그 필요.

### `fatal: matching cipher is not supported`
- 클라이언트가 옛 알고리즘만 제안. `Ciphers +aes256-cbc` (비권장) 또는 클라이언트 업그레이드.

### `Disconnecting: Too many authentication failures for x`
- 위와 동일. 클라이언트 IdentitiesOnly.

---

# 마무리 — 한 페이지로 압축한 SSH

1. **첫 키는 ed25519.** `ssh-keygen -t ed25519`.
2. **두 번째 키는 FIDO2.** `ssh-keygen -t ed25519-sk`.
3. **서버에서 비밀번호 인증은 끈다.** `PasswordAuthentication no`.
4. **agent forwarding 대신 ProxyJump.** `-J bastion`.
5. **반복 접속은 ControlMaster.** `~/.ssh/cm-%C` + 10m persist.
6. **여러 키 있으면 IdentitiesOnly.** 항상.
7. **포트포워딩 세 가지 — -L 끌어오기, -R 밀어보내기, -D SOCKS.**
8. **VPN 흉내는 sshuttle.** -D 의 한계 만나면 거기로.
9. **회사 규모는 SSH CA.** 키 분배 끝.
10. **로그 LogLevel VERBOSE, 모니터는 SIEM, 인증서는 짧게.**

이 열 줄이 책 한 권의 핵심이다. 나머지는 이 위의 스타일이 아니라 디테일이다.

— 끝.
