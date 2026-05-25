---
title: "Linux 명령어 핸드북"
subtitle: "원격 접속·자동화·진단 중심 48강"
author: "Cho Seunghwa"
date: "2026-05"
lang: ko-KR
toc: true
toc-depth: 2
documentclass: book
classoption: oneside
geometry: "margin=2cm"
mainfont: "Noto Sans CJK KR"
monofont: "Noto Sans Mono CJK KR"
---

\newpage

# 머리말

이 책은 리눅스를 **운영의 시점**에서 다룬다. 원격으로 접속하고, 파일을 동기화하고, 무인으로 자동화하고, 막혔을 때 진단한다 — 그 모든 흐름을 한 권으로 묶었다.

`awk`, `bash`, `grep`, `ripgrep`, `vi`, `ls`, `cat` 은 의도적으로 제외했다. 이미 잘 알려진 주제이고, 다른 책에서 충분히 깊이 다룬다. 대신 SSH·rsync·FTP 자동화·각종 진단 도구처럼 **현장에서 자주 쓰지만 묶음 자료가 부족한 영역** 을 본다.

각 장은 같은 흐름이다.

> **개요 → 옵션 표 → 예제 → 자동화 패턴 → 함정**

모든 코드 블록은 그대로 복사해 실행 가능하다. 안드로이드 Termux 환경 차이는 별도 절로 표기한다. 본문에서 `[제N장]` 으로 표시한 부분은 해당 장의 위치를 가리키는 상호참조다.

총 48개 장, 14,000줄, 약 350KB. 처음부터 끝까지 읽기보다는 **목차를 색인처럼** 쓰며 필요할 때 펼치는 책으로 의도했다. 마지막 장의 "주제별 빠른 찾기" 표가 그 색인 역할을 한다.

\newpage

# 통합 목차

## Part 1. 원격 접속과 파일 전송

- 제1장 SSH — ssh, sshd, `~/.ssh/config`
- 제2장 SSH 키와 에이전트
- 제3장 SSH 고급 — ProxyJump, 포트 포워딩, ControlMaster
- 제4장 SSH 자동화 — sshpass, expect, 병렬, 강제 명령
- 제5장 SCP
- 제6장 SFTP
- 제7장 rsync
- 제8장 FTP 와 lftp
- 제9장 FTP 자동화 — .netrc, lftp 스크립트, expect, curl
- 제10장 Telnet — 디버깅 도구로
- 제11장 wget 과 curl

## Part 2. 파일·디렉토리

- 제12장 tree
- 제13장 Midnight Commander (mc)
- 제14장 find 와 xargs
- 제15장 압축과 아카이브 — tar, gzip, bzip2, xz, zip, 7z
- 제16장 링크와 파일 정보 — ln, file, stat, sha256sum

## Part 3. 텍스트 처리

- 제17장 sed
- 제18장 cut / sort / uniq / tr / paste / join
- 제19장 wc / head / tail / less
- 제20장 diff / patch / tee / xxd

## Part 4. 프로세스·시스템

- 제21장 프로세스 — ps, top, htop, pstree
- 제22장 kill 과 시그널
- 제23장 systemd 와 systemctl
- 제24장 journalctl
- 제25장 cron 과 at
- 제26장 screen 과 tmux
- 제27장 nohup, jobs, disown
- 제28장 lsof

## Part 5. 네트워크

- 제29장 ip / ifconfig / route / nmcli
- 제30장 ss 와 netstat
- 제31장 ping / traceroute / mtr
- 제32장 dig / nslookup / host
- 제33장 nc 와 socat
- 제34장 tcpdump
- 제35장 nmap
- 제36장 iptables / nftables / ufw

## Part 6. 권한·보안

- 제37장 chmod / chown / umask
- 제38장 POSIX ACL — setfacl / getfacl
- 제39장 sudo / su / doas
- 제40장 openssl

## Part 7. 디스크·패키지

- 제41장 df / du / mount / lsblk
- 제42장 dd
- 제43장 apt / dpkg
- 제44장 dnf / yum / rpm
- 제45장 pacman / AUR / pkg

## Part 8. 기타 필수

- 제46장 date / watch / sleep / time / timeout
- 제47장 history / alias / env / export
- 제48장 man / info / apropos / tldr

---

## 본문 사용 가이드

본문에서 `[제N장]` 또는 `(제N장 참고)` 같은 표기는 다른 장으로의 상호참조다. PDF로 변환할 경우 Pandoc 의 `\newpage` 가 인식되어 장 단위 페이지 분리가 자동 적용된다. 일반 마크다운 뷰어에서는 단순한 라인 텍스트로 보인다.

\newpage

# 01. SSH 기초

> 원격 셸, 터널링, 파일 전송의 표준. 거의 모든 Linux 운영의 출발점.

## 1.1 SSH 개요

SSH(Secure Shell)는 암호화된 채널로 원격 호스트에 접속하는 프로토콜이자 도구다.

- **클라이언트**: `ssh`, `scp`, `sftp` (OpenSSH 클라이언트 패키지)
- **서버**: `sshd` (OpenSSH 서버 패키지)
- **기본 포트**: TCP 22
- **인증 방식**: 패스워드, 공개키, GSSAPI, 호스트 기반

```bash
# 가장 단순한 접속
ssh user@host

# 포트 지정
ssh -p 2222 user@host

# 명령 실행 후 종료 (인터랙티브 X)
ssh user@host "uptime"

# 다중 명령
ssh user@host "cd /var/log && tail -n 50 messages"
```

## 1.2 ssh 명령 옵션 정리

| 옵션 | 설명 |
|------|------|
| `-p PORT` | 접속 포트 |
| `-l USER` | 로그인 사용자 |
| `-i KEYFILE` | 사용할 개인키 |
| `-o KEY=VAL` | config 옵션을 커맨드라인에서 |
| `-v`, `-vv`, `-vvv` | 디버그 레벨 |
| `-N` | 명령 실행 안 함 (터널 전용) |
| `-f` | 백그라운드 |
| `-T` | TTY 할당 안 함 |
| `-t` | TTY 강제 할당 |
| `-C` | 압축 |
| `-X` | X11 포워딩 |
| `-Y` | 신뢰할 수 있는 X11 |
| `-A` | 에이전트 포워딩 |
| `-L L:H:P` | 로컬 포트 포워딩 |
| `-R R:H:P` | 원격 포트 포워딩 |
| `-D PORT` | 동적 SOCKS 프록시 |
| `-J HOST` | 점프 호스트 (ProxyJump) |
| `-J h1,h2` | 다중 점프 |
| `-q` | 조용히 |
| `-4` / `-6` | IPv4/IPv6 강제 |
| `-F FILE` | 사용자 config 파일 지정 |
| `-G` | config 적용 결과 출력 (실접속 X) |
| `-Q` | 지원 알고리즘 목록 |

## 1.3 첫 접속과 호스트 키

처음 접속하면 서버의 호스트 공개키를 신뢰할지 묻는다.

```
The authenticity of host 'example.com (1.2.3.4)' can't be established.
ED25519 key fingerprint is SHA256:xxxx
Are you sure you want to continue connecting (yes/no/[fingerprint])?
```

`yes`를 입력하면 `~/.ssh/known_hosts`에 저장된다. 이후 동일 호스트의 키가 바뀌면 MITM 의심으로 접속이 차단된다.

```bash
# 특정 호스트의 known_hosts 항목 삭제
ssh-keygen -R example.com

# 파일에서 보기
ssh-keygen -F example.com
```

지문을 사전에 확인하려면:

```bash
ssh-keyscan -t ed25519 example.com
ssh-keyscan example.com | ssh-keygen -lf -
```

## 1.4 ~/.ssh/config — 가장 강력한 무기

매번 옵션을 길게 쓰지 말고 **반드시** config로 정리한다.

```ssh-config
# ~/.ssh/config
Host *
    ServerAliveInterval 60
    ServerAliveCountMax 3
    ControlMaster auto
    ControlPath ~/.ssh/cm-%r@%h:%p
    ControlPersist 10m

Host dev
    HostName dev.internal.example.com
    User seunghwa
    Port 2222
    IdentityFile ~/.ssh/id_ed25519_work
    ForwardAgent yes

Host prod-*
    User deploy
    IdentityFile ~/.ssh/id_ed25519_prod
    ProxyJump bastion

Host bastion
    HostName bastion.example.com
    User jump
    Port 22
```

이제 `ssh dev`, `ssh prod-web1` 처럼 짧게 쓸 수 있다.

### 주요 항목

| 항목 | 설명 |
|------|------|
| `HostName` | 실제 주소 |
| `User` | 사용자 |
| `Port` | 포트 |
| `IdentityFile` | 키 |
| `IdentitiesOnly yes` | 명시한 키만 시도 |
| `ProxyJump` | 점프 호스트 |
| `ProxyCommand` | 프록시 명령 (e.g. nc) |
| `ForwardAgent` | 에이전트 포워딩 |
| `ForwardX11` | X 포워딩 |
| `LocalForward` | -L 과 같음 |
| `RemoteForward` | -R 과 같음 |
| `DynamicForward` | -D 와 같음 |
| `ServerAliveInterval` | keep-alive 초 |
| `ConnectTimeout` | 연결 타임아웃 |
| `StrictHostKeyChecking` | yes/no/accept-new |
| `UserKnownHostsFile` | known_hosts 경로 |
| `ControlMaster` | 연결 다중화 |
| `ControlPath` | 다중화 소켓 |
| `ControlPersist` | 마스터 유지 시간 |

`ssh -G dev` 로 적용 결과를 미리 검증할 수 있다.

## 1.5 sshd (서버 측)

서버 설정 파일: `/etc/ssh/sshd_config`

```sshd-config
Port 22
AddressFamily any
ListenAddress 0.0.0.0
PermitRootLogin prohibit-password
PasswordAuthentication no
PubkeyAuthentication yes
AuthorizedKeysFile .ssh/authorized_keys
ChallengeResponseAuthentication no
UsePAM yes
X11Forwarding yes
PrintMotd no
ClientAliveInterval 120
ClientAliveCountMax 2
AllowUsers seunghwa deploy
Subsystem sftp /usr/lib/openssh/sftp-server
```

설정 변경 후:

```bash
sudo sshd -t                  # 문법 검증
sudo systemctl reload ssh     # debian/ubuntu
sudo systemctl reload sshd    # rhel/fedora
```

### 보안 권장사항

- `PermitRootLogin no` 또는 `prohibit-password`
- `PasswordAuthentication no` (키 인증 후)
- 비표준 포트로 변경하면 봇 스캔 노이즈 감소
- `AllowUsers` / `AllowGroups`로 화이트리스트
- `fail2ban` 설치로 무차별 대입 차단

## 1.6 자주 만나는 에러

| 메시지 | 원인 / 해결 |
|--------|-------------|
| `Permission denied (publickey)` | 서버에 공개키가 없음 또는 권한 문제 |
| `Host key verification failed` | known_hosts 충돌 → `ssh-keygen -R` |
| `Connection refused` | sshd 미동작 또는 방화벽 |
| `Connection timed out` | 라우팅/방화벽/포트 차단 |
| `Too many authentication failures` | 키 너무 많음 → `IdentitiesOnly yes` |
| `WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!` | 호스트 키 변경 (재설치/MITM) |
| `bind: Address already in use` | 포워딩 포트 점유 중 |
| `agent refused operation` | ssh-agent 키 만료 또는 미로드 |

## 1.7 파일 권한 함정

SSH는 권한이 느슨한 키를 거부한다.

```bash
chmod 700 ~/.ssh
chmod 600 ~/.ssh/id_ed25519
chmod 644 ~/.ssh/id_ed25519.pub
chmod 600 ~/.ssh/authorized_keys
chmod 600 ~/.ssh/config
chmod 644 ~/.ssh/known_hosts
```

소유자도 본인이어야 한다.

```bash
chown -R $USER:$USER ~/.ssh
```

## 1.8 디버깅

```bash
ssh -vvv user@host
```

핵심 로그 라인:

- `debug1: Reading configuration data` — 어느 config가 읽히는지
- `debug1: Connecting to ... port 22` — 네트워크 단계
- `debug1: identity file ...` — 시도되는 키 목록
- `debug1: Authentications that can continue: ...` — 서버가 허용한 방식
- `debug1: Offering public key: ...` — 클라이언트가 보내는 키

서버 측은 `journalctl -u ssh -f` 또는 `/var/log/auth.log`.

## 1.9 Termux 특이사항

Termux의 OpenSSH는 동일하지만:

- 안드로이드는 22 포트 listen 시 권한 이슈 → 보통 `8022` 사용
- 키 위치는 `$PREFIX/etc/ssh/` 와 `~/.ssh/` 모두 확인
- `pkg install openssh` 로 설치
- `sshd` 실행 후 `whoami` 와 `passwd` 한 번 설정 필요

```bash
pkg install openssh
sshd
ssh -p 8022 $(whoami)@127.0.0.1
```

## 1.10 자주 쓰는 한 줄 패턴

```bash
# 원격 명령 출력을 로컬 less 로 보기
ssh host "tail -f /var/log/syslog" | less

# 원격 디스크 사용량 정렬
ssh host "du -sh /var/* 2>/dev/null" | sort -h

# 로컬 스크립트를 원격에서 실행 (파일 전송 없이)
ssh host "bash -s" < ./local.sh

# 원격 stdout 을 로컬 파일로
ssh host "tar czf - /etc" > etc-backup.tgz

# 로컬 파일을 원격으로 흘려넣기
cat photo.jpg | ssh host "cat > /tmp/photo.jpg"

# heredoc 으로 다중 명령
ssh host <<'EOF'
  set -e
  cd /opt/app
  git pull
  systemctl restart app
EOF

# 결과 코드 보존
ssh host "exit 7"; echo $?   # → 7
```

다음 챕터: [제2장]

\newpage

---


# 02. SSH 키와 에이전트

> 패스워드 없는 안전한 인증의 기초. 자동화의 전제 조건.

## 2.1 키 인증의 흐름

1. 클라이언트가 자신의 **공개키**를 서버의 `~/.ssh/authorized_keys`에 등록
2. 접속 시 서버가 챌린지를 보내고, 클라이언트가 **개인키**로 서명
3. 서버가 공개키로 검증 → 통과하면 로그인

개인키는 **절대** 외부로 나가서는 안 된다.

## 2.2 ssh-keygen — 키 만들기

```bash
# 권장: ed25519 (작고 빠르고 안전)
ssh-keygen -t ed25519 -C "seunghwa@workstation"

# RSA 가 필요할 때 (구식 서버)
ssh-keygen -t rsa -b 4096 -C "seunghwa@legacy"

# 파일명 지정 (config 의 IdentityFile 과 짝)
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519_work

# 패스프레이즈 없이 (주의: 자동화용에만)
ssh-keygen -t ed25519 -N "" -f ~/.ssh/id_ed25519_bot
```

### ssh-keygen 옵션

| 옵션 | 의미 |
|------|------|
| `-t TYPE` | rsa, ed25519, ecdsa, dsa(폐기) |
| `-b BITS` | 비트 수 (rsa) |
| `-C COMMENT` | 키에 박을 코멘트 |
| `-f FILE` | 출력 파일 |
| `-N PASS` | 패스프레이즈 |
| `-p` | 패스프레이즈 변경 |
| `-y` | 개인키에서 공개키 추출 |
| `-l` | 지문 표시 |
| `-lf FILE` | 파일의 지문 |
| `-R HOST` | known_hosts 항목 제거 |
| `-F HOST` | known_hosts 항목 검색 |
| `-e` | 다른 포맷으로 변환 (PEM, RFC4716) |
| `-o` | OpenSSH 신형 포맷 (기본) |

### 키 종류 비교

| 종류 | 길이 | 속도 | 권장 |
|------|------|------|------|
| ed25519 | 256 | 매우 빠름 | ★ 기본 |
| rsa | 3072~4096 | 보통 | 호환성 |
| ecdsa | 256~521 | 빠름 | 가능하면 피함 |
| dsa | 1024 | — | **금지 (폐기)** |

## 2.3 공개키 등록 — ssh-copy-id

```bash
# 서버 ~/.ssh/authorized_keys 에 자동 추가
ssh-copy-id user@host
ssh-copy-id -i ~/.ssh/id_ed25519_work.pub user@host
ssh-copy-id -p 2222 user@host
```

`ssh-copy-id`가 없으면 수동으로:

```bash
cat ~/.ssh/id_ed25519.pub | ssh user@host \
  'mkdir -p ~/.ssh && chmod 700 ~/.ssh && \
   cat >> ~/.ssh/authorized_keys && \
   chmod 600 ~/.ssh/authorized_keys'
```

### authorized_keys 의 옵션 prefix

```
command="rsync --server ..." ,no-port-forwarding,no-pty ssh-ed25519 AAAA... bot@runner
```

| 옵션 | 효과 |
|------|------|
| `command="..."` | 강제 실행할 명령 (제한 셸) |
| `no-pty` | 터미널 할당 금지 |
| `no-port-forwarding` | 포트 포워딩 금지 |
| `no-X11-forwarding` | X11 금지 |
| `no-agent-forwarding` | 에이전트 포워딩 금지 |
| `from="1.2.3.0/24"` | 접속 출발 IP 제한 |
| `expiry-time="20261231"` | 만료 시각 |

자동화 키는 반드시 `command=`로 묶고 IP 제한을 거는 것이 베스트 프랙티스.

## 2.4 ssh-agent — 키를 메모리에 보관

매번 패스프레이즈를 묻지 않게 에이전트가 메모리에 키를 들고 있다.

```bash
# 에이전트 띄우기
eval "$(ssh-agent -s)"

# 키 등록 (패스프레이즈 한 번)
ssh-add ~/.ssh/id_ed25519
ssh-add ~/.ssh/id_ed25519_work

# 등록된 키 보기
ssh-add -l       # 지문
ssh-add -L       # 공개키 전체

# 모두 제거
ssh-add -D

# 특정 키 제거
ssh-add -d ~/.ssh/id_ed25519_work

# 시간제한 (30분)
ssh-add -t 1800 ~/.ssh/id_ed25519
```

### 셸 시작 시 자동 로드

```bash
# ~/.bashrc 또는 ~/.zshrc
if [ -z "$SSH_AUTH_SOCK" ]; then
  eval "$(ssh-agent -s)" >/dev/null
  ssh-add ~/.ssh/id_ed25519 2>/dev/null
fi
```

### Keychain (멀티 셸 공유)

```bash
sudo apt install keychain
# ~/.bashrc
eval "$(keychain --eval --quiet ~/.ssh/id_ed25519)"
```

여러 터미널에서 동일 에이전트를 공유한다.

### macOS 통합

macOS는 시스템 키체인에 패스프레이즈를 저장 가능:

```bash
ssh-add --apple-use-keychain ~/.ssh/id_ed25519
```

`~/.ssh/config`:

```
Host *
    UseKeychain yes
    AddKeysToAgent yes
    IdentityFile ~/.ssh/id_ed25519
```

## 2.5 에이전트 포워딩

원격 호스트에서 또 다른 호스트로 SSH할 때, 로컬의 에이전트를 통해 인증.

```bash
ssh -A user@bastion
# 베스천 안에서
ssh user@internal   # 로컬 키로 인증됨
```

config:

```
Host bastion
    ForwardAgent yes
```

**주의**: 에이전트 포워딩은 베스천 관리자가 당신의 에이전트 소켓을 통해 다른 호스트에 인증 가능해진다. 신뢰할 수 있는 호스트에만. 더 안전한 대안은 `ProxyJump`.

## 2.6 키 회전과 관리

### 모든 서버의 authorized_keys 점검

```bash
for h in dev prod-web1 prod-web2; do
  echo "=== $h ==="
  ssh "$h" "cat ~/.ssh/authorized_keys"
done
```

### 오래된 키 일괄 제거

```bash
ssh user@host "sed -i '/old@laptop/d' ~/.ssh/authorized_keys"
```

### 새 키 배포 → 검증 → 옛 키 제거 순서

```bash
# 1. 새 키 생성
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519_new -C "rotated-2026-05"

# 2. 모든 서버에 추가 (ssh-copy-id가 중복 방지)
for h in dev prod-web1 prod-web2; do
  ssh-copy-id -i ~/.ssh/id_ed25519_new.pub "$h"
done

# 3. 새 키로 접속 검증
for h in dev prod-web1 prod-web2; do
  ssh -i ~/.ssh/id_ed25519_new -o IdentitiesOnly=yes "$h" "echo OK on $h"
done

# 4. 옛 키 제거
OLDKEY=$(ssh-keygen -lf ~/.ssh/id_ed25519.pub | awk '{print $2}')
for h in dev prod-web1 prod-web2; do
  ssh "$h" "sed -i \"\\#$OLDKEY#d\" ~/.ssh/authorized_keys"
done

# 5. 옛 키 파일 삭제
shred -u ~/.ssh/id_ed25519
mv ~/.ssh/id_ed25519_new ~/.ssh/id_ed25519
mv ~/.ssh/id_ed25519_new.pub ~/.ssh/id_ed25519.pub
```

## 2.7 IdentitiesOnly — "Too many authentication failures"

키를 많이 등록해 두면 SSH가 모두 시도하다가 서버의 `MaxAuthTries` (기본 6)에 걸려 실패한다.

```ssh-config
Host *
    IdentitiesOnly yes      # 명시한 키만 시도
```

또는 명령행:

```bash
ssh -o IdentitiesOnly=yes -i ~/.ssh/id_ed25519_work user@host
```

## 2.8 하드웨어 키 (FIDO/U2F)

YubiKey 등을 SSH 키로:

```bash
ssh-keygen -t ed25519-sk -C "yubikey"      # discoverable=no (resident=no)
ssh-keygen -t ed25519-sk -O resident -C "yubikey"   # 키에 저장됨
```

새 컴퓨터에서 키 가져오기:

```bash
ssh-keygen -K       # 연결된 보안 키에서 키 추출
```

## 2.9 인증서 기반 인증

SSH CA로 서명된 사용자 인증서로 키 분배 부담 제거.

```bash
# CA 키 생성 (한 번)
ssh-keygen -t ed25519 -f ~/.ssh/ca

# 사용자 공개키 서명
ssh-keygen -s ~/.ssh/ca -I "seunghwa@2026" \
  -n seunghwa,deploy -V +52w \
  ~/.ssh/id_ed25519.pub
# → id_ed25519-cert.pub 생성
```

서버 `/etc/ssh/sshd_config`:

```
TrustedUserCAKeys /etc/ssh/ca.pub
```

이제 모든 서버가 CA 공개키 하나만 알면 된다. 인증서에 만료를 박아 자동 회전 가능.

## 2.10 자주 쓰는 진단 명령

```bash
# 어떤 키들이 시도되는지
ssh -v user@host 2>&1 | grep -i "offering\|identity"

# 서버가 받는 공개키 지문 (서버 측)
sudo journalctl -u ssh | grep "Accepted publickey"

# 키 파일의 지문
ssh-keygen -lf ~/.ssh/id_ed25519.pub

# 에이전트가 들고 있는 키들의 지문
ssh-add -l
```

다음 챕터: [제3장]

\newpage

---


# 03. SSH 고급 — 점프, 터널, 포워딩

> 베스천 너머의 서버, DB 포트 노출, SOCKS 프록시, 다중화까지.

## 3.1 ProxyJump — 점프 호스트

베스천(점프 서버)을 거쳐 내부 호스트에 접속.

```bash
# 한 줄
ssh -J bastion internal

# 다중 점프
ssh -J bastion1,bastion2 deepest

# 점프에서 다른 사용자/포트
ssh -J jumpuser@bastion:2222 user@internal
```

config:

```ssh-config
Host bastion
    HostName bastion.example.com
    User jump

Host internal
    HostName 10.0.5.10
    User app
    ProxyJump bastion
```

이제 `ssh internal` 한 번이면 끝.

### ProxyCommand (구식이지만 여전히 유용)

`netcat` 또는 `ssh -W`로 직접 프록시.

```ssh-config
Host internal
    HostName 10.0.5.10
    ProxyCommand ssh bastion -W %h:%p
```

`%h`는 HostName, `%p`는 Port.

### ProxyJump vs ProxyCommand

- **ProxyJump**: 깔끔, 기본 권장
- **ProxyCommand**: 임의 명령(예: `corkscrew` HTTP 프록시 통과) 필요 시

## 3.2 포트 포워딩

### 로컬 포워딩 -L

원격에서만 접근 가능한 서비스를 로컬에 노출.

```bash
# 원격 DB(3306) 를 로컬 13306 으로
ssh -L 13306:localhost:3306 user@dbhost
# → mysql -h 127.0.0.1 -P 13306
```

문법: `-L [bind_addr:]local_port:remote_host:remote_port`

```bash
# 모든 인터페이스에 바인드(주의)
ssh -L 0.0.0.0:13306:localhost:3306 user@dbhost

# 베스천 거쳐 내부 DB 로
ssh -L 13306:internal-db:3306 user@bastion
```

### 원격 포워딩 -R

로컬 서비스를 원격에 노출 (역터널).

```bash
# 로컬 8080 을 원격 9090 에 노출
ssh -R 9090:localhost:8080 user@public-host
# 원격에서: curl localhost:9090 → 로컬 8080 도달
```

문법: `-R [bind_addr:]remote_port:target_host:target_port`

`sshd_config` 에서 `GatewayPorts yes` 가 있어야 외부 인터페이스에 바인드 가능.

### 동적 포워딩 -D (SOCKS 프록시)

```bash
ssh -D 1080 user@host
# 브라우저 SOCKS5 프록시 = 127.0.0.1:1080
```

원격 네트워크에서 모든 트래픽을 통과시키는 만능 터널.

```bash
# curl 로 SOCKS 통과
curl --socks5 localhost:1080 https://internal.example.com
```

### -N -f 조합 (백그라운드 터널)

```bash
ssh -fNL 13306:localhost:3306 user@dbhost
# 셸 없이 터널만 백그라운드로
```

종료:

```bash
pkill -f "ssh -fNL 13306"
# 또는 ControlPath 사용 시
ssh -O exit dbhost
```

### config 로 항상 자동 터널

```ssh-config
Host dbhost
    HostName db.internal
    User app
    LocalForward 13306 localhost:3306
    LocalForward 16379 localhost:6379
```

`ssh dbhost` 만 해도 두 터널이 자동 생성.

## 3.3 X11 포워딩

GUI 앱을 원격에서 실행, 화면은 로컬.

```bash
ssh -X user@host
ssh -Y user@host    # 신뢰 모드 (보안 검사 완화, 빠름)

# 원격에서
xclock &
firefox &
```

서버 `/etc/ssh/sshd_config`:

```
X11Forwarding yes
X11UseLocalhost yes
```

로컬에 X 서버가 떠 있어야 한다 (Linux는 기본, macOS는 XQuartz, Windows는 VcXsrv/X410).

## 3.4 ControlMaster — 연결 다중화

여러 ssh 호출이 같은 호스트에 갈 때 첫 연결만 인증하고 나머지는 재사용 → 빠르다.

```ssh-config
Host *
    ControlMaster auto
    ControlPath ~/.ssh/cm-%r@%h:%p
    ControlPersist 10m
```

`ControlPersist 10m`: 마지막 연결 종료 후 10분간 마스터 유지.

### 마스터 제어

```bash
ssh -O check host    # 마스터 살아있는지 확인
ssh -O exit host     # 마스터 종료
ssh -O stop host     # 새 연결 안 받음
```

### 효과

`scp file1 host:`, `scp file2 host:`, `ssh host cmd` 가 다 같은 TCP+SSH 세션을 공유 → 인증 한 번이면 충분.

## 3.5 Keep-Alive — 끊김 방지

NAT 타임아웃으로 SSH가 끊어지는 문제.

### 클라이언트 측

```ssh-config
Host *
    ServerAliveInterval 60
    ServerAliveCountMax 3
    TCPKeepAlive yes
```

60초마다 ping, 3번 응답 없으면 끊는다.

### 서버 측 (sshd_config)

```
ClientAliveInterval 60
ClientAliveCountMax 3
```

## 3.6 SSH 압축

저속 회선에서 유효:

```bash
ssh -C user@host
```

config:

```
Compression yes
```

빠른 회선에선 CPU만 먹어 오히려 손해. 최근에는 거의 의미 없음.

## 3.7 escape 시퀀스

SSH 세션 안에서 특수 명령 (기본 escape: `~`).

```
~?    # 도움말
~.    # 강제 종료 (좀비 세션 죽일 때)
~^Z   # SSH 자체를 백그라운드로
~~    # 리터럴 ~ 입력
~#    # 활성 포워딩 목록
~C    # 명령 모드 (포워딩 추가/제거)
```

`~C` 안에서:
```
ssh> -L 19999:localhost:9999
Forwarding port.
ssh> -KL 19999
Cancelled.
```

세션 도중에 포트 포워딩을 동적으로 추가/제거 가능.

## 3.8 SSHFS — 원격 디렉토리를 마운트

```bash
sudo apt install sshfs

mkdir ~/remote
sshfs user@host:/var/www ~/remote
ls ~/remote     # 원격 파일이 로컬처럼 보임

# 언마운트
fusermount -u ~/remote     # linux
umount ~/remote            # mac (macFUSE)
```

옵션:

```bash
sshfs -o reconnect,ServerAliveInterval=15,ServerAliveCountMax=3 \
      -o IdentityFile=~/.ssh/id_ed25519 \
      user@host:/data ~/remote
```

## 3.9 Mosh — 모바일 SSH

```bash
sudo apt install mosh
mosh user@host
```

UDP 기반이라 IP가 바뀌어도 세션 유지(노트북 슬립/모바일 전환).

서버에 mosh가 설치되어 있어야 하고 UDP 60000-61000 포트 개방 필요.

## 3.10 베스천 활용 패턴

### 패턴 1. 단순 점프

```ssh-config
Host bastion
    HostName b.example.com
    User jump
    IdentityFile ~/.ssh/id_ed25519

Host prod-*
    User deploy
    IdentityFile ~/.ssh/id_ed25519_prod
    ProxyJump bastion
```

### 패턴 2. CIDR 매칭

```ssh-config
Host 10.0.*
    ProxyJump bastion
    User deploy
```

`ssh 10.0.5.10` 자동으로 베스천 경유.

### 패턴 3. 다중 베스천 (지역별)

```ssh-config
Host *.kr.internal
    ProxyJump bastion-kr

Host *.us.internal
    ProxyJump bastion-us
```

### 패턴 4. SOCKS over Bastion

```bash
ssh -D 1080 -N bastion
# 모든 내부망 트래픽을 로컬 1080 SOCKS 로
```

브라우저 SOCKS 설정 → 내부 웹앱 접근.

## 3.11 디버깅 체크리스트

```bash
# config 적용 결과
ssh -G host

# 어떤 키 시도?
ssh -v host 2>&1 | grep -E "Offering|Trying"

# 어떤 ProxyJump 발동?
ssh -v host 2>&1 | grep -i proxy

# 서버 키 알고리즘 협상
ssh -v host 2>&1 | grep -i "kex\|cipher"

# 로컬 포워딩 살아있는지
ss -ltnp | grep 13306

# 다중화 마스터 동작 중?
ssh -O check host
```

다음 챕터: [제4장]

\newpage

---


# 04. SSH 자동화

> 사용자 입력 없이 SSH로 원격 명령을 실행하는 모든 패턴.

## 4.1 자동화 전 체크리스트

| 항목 | 권장 |
|------|------|
| 인증 | 키 인증 + 패스프레이즈 없음 또는 ssh-agent |
| StrictHostKeyChecking | 사전에 known_hosts 채워두기 |
| BatchMode | `yes` (프롬프트 시 즉시 실패) |
| 로깅 | `-v` 출력을 캡처 |
| 종료 코드 | 원격 코드를 그대로 보존 |
| 권한 | 자동화 키는 `command=` 로 제한 |

기본 자동화 옵션 세트:

```bash
SSH_OPTS=(
  -o BatchMode=yes
  -o ConnectTimeout=10
  -o ServerAliveInterval=30
  -o StrictHostKeyChecking=accept-new
)
ssh "${SSH_OPTS[@]}" user@host "uptime"
```

`accept-new`는 새 호스트는 자동 추가하되 변경된 키는 거부한다(가장 안전한 자동화 모드).

## 4.2 known_hosts 사전 채우기

```bash
ssh-keyscan -t ed25519,rsa host1 host2 host3 >> ~/.ssh/known_hosts
sort -u ~/.ssh/known_hosts -o ~/.ssh/known_hosts
```

CI 환경에서:

```bash
mkdir -p ~/.ssh
chmod 700 ~/.ssh
ssh-keyscan -t ed25519 deploy.example.com > ~/.ssh/known_hosts
chmod 600 ~/.ssh/known_hosts
```

지문을 사전에 알고 있다면 검증까지:

```bash
EXPECTED="SHA256:xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
GOT=$(ssh-keyscan -t ed25519 host 2>/dev/null | ssh-keygen -lf - | awk '{print $2}')
[ "$GOT" = "$EXPECTED" ] || { echo "Fingerprint mismatch"; exit 1; }
ssh-keyscan -t ed25519 host >> ~/.ssh/known_hosts
```

## 4.3 sshpass — 패스워드 자동화 (최후의 수단)

키 인증이 불가능한 레거시 환경에서만.

```bash
sudo apt install sshpass

# 패스워드를 명령행에 (가장 위험, ps에 노출)
sshpass -p 'PW' ssh user@host

# 환경 변수에서 (조금 낫지만 여전히 위험)
SSHPASS='PW' sshpass -e ssh user@host

# 파일에서 (가장 안전, 권한 600)
sshpass -f ~/.secret/pw.txt ssh user@host
```

`sshpass`는 절대 키 인증의 대체로 쓰지 말 것. 키가 가능한 환경이라면 키로.

scp/rsync 와 결합:

```bash
sshpass -f /etc/.appsync.pw scp -o BatchMode=no file user@host:/tmp/
sshpass -f /etc/.appsync.pw rsync -avz src/ user@host:/dst/
```

## 4.4 expect — 인터랙티브 자동화

비밀번호 외에 yes/no, 메뉴 응답까지 자동화.

```bash
sudo apt install expect
```

### 기본 패턴

```tcl
#!/usr/bin/env expect
set timeout 20
set host   [lindex $argv 0]
set pw     [lindex $argv 1]

spawn ssh user@$host
expect {
  "yes/no" { send "yes\r"; exp_continue }
  "password:" { send "$pw\r" }
}
expect "$ "
send "uptime\r"
expect "$ "
send "exit\r"
expect eof
```

실행:

```bash
chmod +x auto.exp
./auto.exp prod-web1 'mypw'
```

### 자주 쓰는 expect 구문

| 구문 | 의미 |
|------|------|
| `spawn CMD` | 자식 프로세스 시작 |
| `send "STR\r"` | 문자열 전송 (\r = Enter) |
| `expect "PAT"` | 패턴 대기 |
| `expect { ... }` | 다중 패턴 분기 |
| `exp_continue` | 같은 expect 블록 다시 |
| `set timeout N` | 대기 제한 |
| `interact` | 사용자에게 제어 넘김 |
| `expect eof` | 자식 종료 대기 |

### 패스워드 + sudo 자동화

```tcl
#!/usr/bin/env expect
set timeout 30
set host [lindex $argv 0]
set pw   [lindex $argv 1]

spawn ssh -t user@$host
expect "password:"
send "$pw\r"
expect "$ "
send "sudo systemctl restart nginx\r"
expect {
  "password for" { send "$pw\r"; exp_continue }
  "$ " {}
}
send "exit\r"
expect eof
```

`-t`로 sudo가 TTY를 요구해도 동작.

### 보안 팁

- 스크립트는 `chmod 700`
- 패스워드는 `expect_user`로 입력 받거나, `secret-tool`(libsecret) 활용
- 다중 호스트라면 결과를 로그 파일로

```tcl
log_file -a /var/log/auto-ssh.log
```

## 4.5 BatchMode 와 종료 코드

```bash
ssh -o BatchMode=yes user@host "false"
echo $?     # → 1 (원격 종료 코드)

ssh -o BatchMode=yes nonexistent "true"
echo $?     # → 255 (SSH 자체 실패)
```

종료 코드 255는 SSH 연결/인증 실패임을 기억하라. 스크립트에서:

```bash
if ! ssh -o BatchMode=yes "$h" "true" 2>/dev/null; then
  echo "$h: 접속 불가"
  continue
fi
```

## 4.6 다중 호스트 병렬 실행

### 단순 for 루프 (직렬)

```bash
for h in web1 web2 web3 db1; do
  echo "=== $h ==="
  ssh -o BatchMode=yes "$h" "uptime"
done
```

### xargs 로 병렬

```bash
echo -e "web1\nweb2\nweb3\ndb1" | \
  xargs -P 8 -I {} ssh -o BatchMode=yes {} "uptime"
```

`-P 8`: 동시 8개. 출력이 섞이므로 호스트 라벨을 같이.

```bash
echo -e "web1\nweb2\nweb3" | \
  xargs -P 4 -I {} sh -c 'ssh -o BatchMode=yes {} "uptime" | sed "s/^/{}: /"'
```

### parallel-ssh / pdsh

```bash
sudo apt install pssh        # parallel-ssh
pssh -h hosts.txt -i "uptime"

sudo apt install pdsh
pdsh -w web[1-3],db1 "uptime"
```

`hosts.txt`:
```
user@web1
user@web2
user@web3
```

### GNU parallel

```bash
parallel -j 8 ssh {} "uptime" ::: web1 web2 web3 db1
parallel -j 8 --tag ssh {} "uptime" :::: hosts.txt
```

`--tag`가 호스트명을 자동으로 prefix 해 준다.

## 4.7 명령 실행 — heredoc, 스크립트 흘려넣기

### 짧은 명령

```bash
ssh host "command1; command2 && command3"
```

세미콜론은 항상 실행, `&&`은 앞이 성공해야.

### 다중 라인 heredoc

```bash
ssh host bash <<'EOF'
set -euo pipefail
cd /opt/app
git fetch --all
git reset --hard origin/main
./deploy.sh
EOF
```

`<<'EOF'`(따옴표): 로컬 변수 확장 안 됨. 보통 이게 안전.
`<<EOF`(따옴표 X): 로컬 변수 확장 됨.

```bash
TARGET="/opt/app"
ssh host bash <<EOF
cd $TARGET
git pull
EOF
```

### 로컬 스크립트 흘려넣기

```bash
ssh host "bash -s" < ./deploy.sh
ssh host "bash -s -- arg1 arg2" < ./deploy.sh
```

스크립트 안에서 `$1`, `$2`로 인자 사용.

### 결과 받기

```bash
RESULT=$(ssh host "uptime")
echo "$RESULT"
```

## 4.8 강제 명령 (authorized_keys 의 command=)

자동화용 키는 항상 명령을 강제하라.

```
# ~/.ssh/authorized_keys
command="/usr/local/bin/deploy.sh",no-pty,no-port-forwarding,from="10.0.0.0/8" ssh-ed25519 AAAA... bot@ci
```

이 키로 접속하면 원격 셸이 아니라 `deploy.sh` 만 실행된다.

`deploy.sh`에서 클라이언트가 보낸 명령을 검사:

```bash
#!/bin/bash
case "$SSH_ORIGINAL_COMMAND" in
  "deploy")    /opt/app/deploy.sh ;;
  "rollback")  /opt/app/rollback.sh ;;
  "status")    systemctl status app ;;
  *) echo "denied: $SSH_ORIGINAL_COMMAND"; exit 1 ;;
esac
```

클라이언트:

```bash
ssh bot@host deploy
ssh bot@host status
```

특정 동작만 허용되고, 셸은 절대 못 얻는다.

## 4.9 Ansible 스타일 (잠깐)

대규모 자동화는 Ansible이 정답이지만, 기본 SSH 자동화 위에 올라간다.

```yaml
# playbook.yml
- hosts: web
  tasks:
    - name: nginx restart
      service: { name: nginx, state: restarted }
      become: yes
```

```bash
ansible-playbook -i inventory playbook.yml
```

내부적으로는 `ssh -o ControlMaster=auto` 로 다중화하며 SFTP/SCP 로 파일을 전송한다. 즉 이 책의 기본기를 알면 Ansible도 같은 패턴.

## 4.10 자주 쓰는 자동화 한 줄들

```bash
# 모든 서버 디스크 사용량
for h in $(< hosts.txt); do
  printf "%-20s " "$h"
  ssh "$h" "df -h / | awk 'NR==2{print \$5}'"
done

# 변경된 설정 파일 일괄 배포
for h in web1 web2 web3; do
  scp nginx.conf "$h":/tmp/nginx.conf
  ssh "$h" "sudo mv /tmp/nginx.conf /etc/nginx/nginx.conf && \
            sudo nginx -t && sudo systemctl reload nginx"
done

# 원격 명령을 모두 백그라운드로 (병렬 + 결과 수집)
declare -A pids
declare -A logs
for h in web1 web2 web3; do
  log=$(mktemp)
  ssh "$h" "uptime" > "$log" 2>&1 &
  pids[$h]=$!
  logs[$h]=$log
done
for h in "${!pids[@]}"; do
  wait "${pids[$h]}"
  echo "=== $h ==="; cat "${logs[$h]}"; rm "${logs[$h]}"
done

# 원격 호스트에서 로컬로 패키지 설치 자동
ssh -tt host "sudo apt-get update && sudo apt-get install -y htop"
# -tt 는 sudo 가 TTY 를 요구해도 통과
```

## 4.11 흔한 함정

| 함정 | 대처 |
|------|------|
| 패스프레이즈 키를 자동화에 사용 | 자동화 전용 키 분리, ssh-agent |
| `StrictHostKeyChecking=no` 남발 | `accept-new` 사용, known_hosts 사전 |
| 패스워드를 스크립트에 박음 | `sshpass -f`, expect의 stdin, vault |
| 한 키로 모든 서버 | 키 분리, `command=`+IP 제한 |
| 종료 코드 255를 성공으로 오해 | `ssh ... && ...` 대신 명시적 체크 |
| 원격 한글 깨짐 | `LANG=C.UTF-8 ssh ...` 또는 SendEnv |

다음 챕터: [제5장]

\newpage

---


# 05. SCP — 단순 파일 복사

> SSH 위에서 동작하는 가장 단순한 복사 도구. 한 번 던지고 끝.

## 5.1 SCP 개요

`scp`는 SSH 세션을 열고 그 위에서 파일을 복사한다. 옵션 다수가 `ssh`와 호환된다.

> **참고**: OpenSSH 9.0 이상부터 `scp`는 내부적으로 SFTP 프로토콜을 쓴다. 동작은 거의 같지만 일부 옵션 의미가 변했다.

```bash
# 로컬 → 원격
scp local.txt user@host:/path/

# 원격 → 로컬
scp user@host:/path/file.txt ./

# 원격 → 원격 (3-party)
scp user1@a:/f user2@b:/dst/
```

## 5.2 옵션 정리

| 옵션 | 설명 |
|------|------|
| `-r` | 디렉토리 재귀 |
| `-P PORT` | 포트 (대문자!) |
| `-i KEY` | 개인키 |
| `-p` | 시간/권한 보존 |
| `-q` | 진행 표시 끄기 |
| `-C` | 압축 |
| `-l LIMIT` | 대역폭 제한 (Kbit/s) |
| `-3` | 로컬 경유 3-party (기본은 직접) |
| `-J HOST` | 점프 호스트 |
| `-o KEY=VAL` | ssh 옵션 |
| `-F FILE` | ssh config 파일 |
| `-O` | 구식 (SCP) 프로토콜 강제 |
| `-s` | SFTP 프로토콜 강제 |
| `-T` | 파일명 검증 비활성 |
| `-v`, `-vv` | 디버그 |

`ssh`는 `-p`가 포트, `scp`는 `-p`가 권한 보존, **포트는 대문자 `-P`**. 외워둘 것.

## 5.3 기본 예제

```bash
# 단일 파일
scp report.pdf user@host:/home/user/

# 이름 바꿔서
scp report.pdf user@host:/home/user/r-2026-05.pdf

# 디렉토리 통째로
scp -r ./project/ user@host:/srv/

# 와일드카드 (로컬 셸이 확장)
scp ./logs/*.gz user@host:/backup/

# 와일드카드 (원격에서 확장하려면 따옴표)
scp 'user@host:/var/log/*.log' ./

# 권한/타임스탬프 보존
scp -p file user@host:/dst/

# 비표준 포트
scp -P 2222 file user@host:/dst/

# 키 지정
scp -i ~/.ssh/id_ed25519_work file user@host:/dst/
```

## 5.4 ~/.ssh/config 활용

config에 정의된 호스트 별칭은 그대로 통한다.

```ssh-config
Host dev
    HostName dev.internal
    User seunghwa
    Port 2222
    IdentityFile ~/.ssh/id_ed25519_work
```

```bash
scp build.tar.gz dev:/tmp/
scp -r dev:/var/log/app/ ./logs/
```

옵션 매번 붙이지 말고 config로.

## 5.5 점프 호스트 경유

```bash
scp -J bastion file user@internal:/tmp/
scp -J jump1,jump2 file user@deepest:/tmp/
```

config로:

```ssh-config
Host internal
    HostName 10.0.5.10
    User app
    ProxyJump bastion
```

```bash
scp file internal:/tmp/    # 자동으로 bastion 경유
```

## 5.6 진행 표시 / 대역폭 제한

```bash
# 진행 막대 (기본 표시됨)
scp big.iso host:/tmp/

# 표시 끄기
scp -q big.iso host:/tmp/

# 대역폭 1Mbit/s
scp -l 1024 big.iso host:/tmp/
```

업무 시간 백업 등에 `-l`이 유용.

## 5.7 3-party 복사

```bash
# 직접 (기본): A → B 직접 전송, 로컬은 중계만
scp user1@a:/f user2@b:/dst/

# 로컬 경유
scp -3 user1@a:/f user2@b:/dst/
```

A↔B 직접 통신이 막혀 있다면 `-3`으로 로컬 경유.

## 5.8 SCP의 한계 — rsync로 가야 할 때

| 한계 | 설명 |
|------|------|
| 재시도 없음 | 네트워크 끊기면 처음부터 |
| 부분 전송 없음 | 일부만 변경된 큰 파일도 전부 재전송 |
| 동기화 아님 | 원격에만 있는 파일 삭제 못 함 |
| 진행률 부정확 | 큰 트리에서 의미 없음 |
| 메타데이터 한계 | xattr, ACL 등 보존 어려움 |

→ 반복 동기화는 [제7장]. SCP는 일회성/단순 복사.

## 5.9 자주 쓰는 패턴

```bash
# 다수 호스트에 같은 파일
for h in web1 web2 web3; do
  scp config.yml "$h":/etc/app/
done

# 다수 호스트에서 같은 파일을 가져와 라벨링
for h in web1 web2 web3; do
  scp "$h":/var/log/app/error.log "./error-$h.log"
done

# heredoc 으로 작성한 파일을 곧장 원격으로
cat <<EOF | ssh host "cat > /tmp/note.md"
# 메모
오늘의 작업
EOF
# (scp 가 stdin 입력은 못 받으므로 ssh 사용)

# tar 로 묶어서 한 번에 (작은 파일 多 → 빠름)
tar czf - dir/ | ssh host "tar xzf - -C /dst/"

# 받기
ssh host "tar czf - /var/log/app" | tar xzf - -C ./backup/
```

## 5.10 Termux 특이사항

- 기본 포트가 8022인 sshd 와 페어
- 안드로이드 외부 저장소 (`/storage/emulated/0/...`)는 SAF 정책상 권한이 까다로움
- `termux-setup-storage` 후 `~/storage/...` 심볼릭 링크 사용 권장

```bash
scp -P 8022 file 192.168.0.10:/data/data/com.termux/files/home/
# 또는
scp -P 8022 file 192.168.0.10:storage/shared/Download/
```

## 5.11 디버깅

```bash
scp -v file host:/tmp/ 2>&1 | head -40

# 권한 / 경로 문제: 원격에 미리 mkdir
ssh host "mkdir -p /srv/incoming"
scp file host:/srv/incoming/

# 파일명에 공백/한글
scp 'file with space.txt' host:'"/tmp/with space/"'
```

원격 경로의 셸 확장도 고려해야 한다. 따옴표 두 번(로컬+원격) 거는 게 안전.

다음 챕터: [제6장]

\newpage

---


# 06. SFTP — 보안 파일 전송 프로토콜

> SSH 위에서 동작하는 인터랙티브 파일 전송. FTP의 안전한 후계자.

## 6.1 SFTP 개요

- SSH 프로토콜의 서브시스템(`Subsystem sftp`)
- 한 번의 연결로 다중 파일 전송, 디렉토리 탐색, 권한 변경 등
- FTP와 명령 체계는 비슷하지만 단일 암호화 채널만 사용 (방화벽 친화적)
- 레쥼(이어받기) 지원 (`reget`, `reput`)
- chroot 격리로 파일 전송 전용 사용자 만들기 쉬움

## 6.2 인터랙티브 사용

```bash
sftp user@host
sftp -P 2222 user@host
sftp -i ~/.ssh/id_ed25519_work user@host
sftp -J bastion user@internal
```

프롬프트:

```
sftp>
```

### 핵심 명령

| 명령 | 의미 |
|------|------|
| `pwd` / `lpwd` | 원격/로컬 현재 디렉토리 |
| `cd` / `lcd` | 원격/로컬 이동 |
| `ls` / `lls` | 원격/로컬 목록 |
| `mkdir` / `lmkdir` | 디렉토리 생성 |
| `rmdir` | 빈 디렉토리 삭제 |
| `rm` | 파일 삭제 |
| `rename SRC DST` | 이름 변경 |
| `chmod MODE FILE` | 권한 |
| `chown UID FILE` | 소유자 |
| `chgrp GID FILE` | 그룹 |
| `ln -s TARGET LINK` | 심볼릭 링크 |
| `get FILE [LOCAL]` | 다운로드 |
| `put FILE [REMOTE]` | 업로드 |
| `mget PAT` | 다중 다운로드 |
| `mput PAT` | 다중 업로드 |
| `reget FILE` | 이어받기 |
| `reput FILE` | 이어 올리기 |
| `df [-h]` | 디스크 |
| `version` | 프로토콜 버전 |
| `progress` | 진행 표시 토글 |
| `!CMD` | 로컬 셸 명령 |
| `bye` / `quit` / `exit` | 종료 |

### 다운/업로드 옵션

```
get -P file       # 권한/타임스탬프 보존
get -r dir/       # 재귀
get -a file       # append (이어받기)
put -P file
put -r dir/
```

### 와일드카드

```
sftp> mget *.log
sftp> mput config/*.yml
```

서버 측 셸이 아닌 SFTP 자체가 글로빙하므로 백슬래시/따옴표 규칙이 셸과 다르다.

## 6.3 batch 모드 — 자동화

스크립트로 실행할 명령 목록 작성.

`/path/to/sftp.cmd`:
```
cd /upload
lcd /var/output
mput *.csv
bye
```

실행:

```bash
sftp -b /path/to/sftp.cmd user@host
```

### 옵션과 종료 코드

```bash
sftp -b commands.txt -i ~/.ssh/key user@host
echo $?    # 0 성공, 그 외 실패
```

| 옵션 | 의미 |
|------|------|
| `-b FILE` | batch 파일 (`-` = stdin) |
| `-P PORT` | 포트 |
| `-i KEY` | 키 |
| `-o KEY=VAL` | ssh 옵션 |
| `-r` | get/put 기본 재귀 (OpenSSH 9+) |
| `-a` | 이어받기 기본 |
| `-f` | 매 put 후 fsync |
| `-q` | 조용히 |
| `-v` | 디버그 |
| `-J HOST` | 점프 호스트 |
| `-D PROG` | 다른 SFTP 서버 직접 실행 |

### stdin 으로 batch

```bash
sftp -b - user@host <<'EOF'
cd /incoming
put report.csv
chmod 640 report.csv
bye
EOF
```

### 에러 무시

기본은 한 명령 실패 시 즉시 종료. 무시하려면 명령 앞에 `-`:

```
-rm /tmp/old.tmp
put new.tmp /tmp/
```

## 6.4 진행과 검증

```bash
sftp> progress     # on/off 토글
sftp> get -P big.iso
Fetching /remote/big.iso to ./big.iso
big.iso     56%   500MB   12.3MB/s   00:32 ETA
```

전송 후 해시 검증:

```bash
ssh host "sha256sum /remote/file" > expected.txt
sha256sum local-file > actual.txt
diff expected.txt actual.txt
```

## 6.5 SFTP 전용 사용자 (chrooted)

원격 사용자에게 셸은 못 주고 파일 전송만 허용.

`/etc/ssh/sshd_config`:

```
Match Group sftponly
    ChrootDirectory /srv/sftp/%u
    ForceCommand internal-sftp
    AllowTcpForwarding no
    X11Forwarding no
    PermitTunnel no
```

준비:

```bash
sudo groupadd sftponly
sudo useradd -m -g sftponly -s /usr/sbin/nologin upload1
sudo passwd upload1                    # 또는 키 등록

# chroot 디렉토리는 root 소유 + 755 여야 함 (sshd 강제)
sudo mkdir -p /srv/sftp/upload1/incoming
sudo chown root:root /srv/sftp /srv/sftp/upload1
sudo chmod 755 /srv/sftp /srv/sftp/upload1
sudo chown upload1:sftponly /srv/sftp/upload1/incoming

sudo systemctl reload ssh
```

```bash
sftp upload1@host
# / → 격리된 공간만 보임
```

## 6.6 ProxyJump / 점프 호스트

```bash
sftp -J bastion user@internal
```

config에 정의되어 있으면:

```bash
sftp internal:/path/file ./
```

처럼 짧게 가능.

## 6.7 SSH config 옵션이 그대로 적용

```ssh-config
Host upload
    HostName ftp.example.com
    User upload1
    IdentityFile ~/.ssh/upload_key
    IdentitiesOnly yes
    Port 2222
    PreferredAuthentications publickey
```

```bash
sftp upload
sftp -b cmds.txt upload
```

## 6.8 GUI 클라이언트 호환

같은 SSH 키/계정으로 다음과 호환:

- **FileZilla** — 'SFTP - SSH File Transfer Protocol' 선택
- **WinSCP** — Windows
- **Cyberduck** — macOS
- **Nautilus / Files** — `sftp://user@host/path`

CLI 자동화와 GUI 가벼운 작업을 같은 계정으로 운영 가능.

## 6.9 자주 쓰는 자동화 패턴

### 일일 리포트 업로드

```bash
#!/bin/bash
set -euo pipefail
DATE=$(date +%F)
LOCAL=/var/reports/daily-$DATE.csv

sftp -b - upload <<EOF
cd /incoming
put $LOCAL
bye
EOF

logger "report $DATE uploaded"
```

cron:
```
0 6 * * * /usr/local/bin/upload-report.sh
```

### 원격 → 로컬 폴더 미러 (한 번만)

```bash
sftp -b - user@host <<'EOF'
lcd /var/incoming
get -r /remote/data
bye
EOF
```

(반복 동기화는 rsync가 정답)

### 업로드 후 원격에서 처리 트리거

```bash
sftp -b - user@host <<'EOF'
put report.csv /upload/report.csv.tmp
rename /upload/report.csv.tmp /upload/report.csv
bye
EOF
```

`.tmp` → 실제명으로 원자적 rename → 서버 측 watcher가 완성된 파일만 처리.

## 6.10 로깅과 감사

서버 `/etc/ssh/sshd_config`:

```
Subsystem sftp internal-sftp -l INFO
Match Group sftponly
    ChrootDirectory /srv/sftp/%u
    ForceCommand internal-sftp -l VERBOSE
```

`journalctl -u ssh | grep sftp`에서 누가 무엇을 올리고 받았는지 확인 가능.

## 6.11 FTP 대비 SFTP 의 장점

| 항목 | FTP | SFTP |
|------|-----|------|
| 암호화 | 없음 (FTPS 별도) | 항상 |
| 포트 | 21 + 데이터 포트 다수 | 22 단일 |
| 방화벽 | NAT/PASV 트러블 | 단순 |
| 파일 메타데이터 | 제한적 | 완전 |
| 인증 | 기본 평문 | 키 기반 |
| 재개 | 일부 지원 | reget/reput |
| chroot | vsftpd 등 별도 설정 | sshd 단일 설정 |

특별한 이유 없으면 항상 SFTP.

다음 챕터: [제7장]

\newpage

---


# 07. rsync — 동기화의 표준

> 변경된 부분만 보내는 똑똑한 복사. 백업·배포·미러링의 기본기.

## 7.1 rsync 가 특별한 이유

- **델타 전송**: 변경된 블록만 보냄. 큰 파일 일부 수정 → 적은 트래픽
- **재시도/재개**: `--partial` 로 끊겨도 이어감
- **속성 보존**: 권한/시간/링크/특수 파일/xattr/ACL
- **삭제 동기화**: `--delete` 로 원본에 없는 것 제거
- **전송 모드 다양**: 로컬, SSH 위, rsync 데몬

```bash
rsync SRC DST
rsync user@host:SRC LOCAL
rsync LOCAL user@host:DST
rsync host::module/path LOCAL    # rsync 데몬
```

## 7.2 옵션 정리 (자주 쓰는 것 위주)

| 옵션 | 의미 |
|------|------|
| `-a` | archive: `-rlptgoD` 묶음 (기본 권장) |
| `-r` | 재귀 |
| `-l` | 심볼릭 링크 그대로 복사 |
| `-p` | 권한 |
| `-t` | 타임스탬프 |
| `-g` | 그룹 |
| `-o` | 소유자 |
| `-D` | 디바이스/특수 파일 |
| `-A` | ACL |
| `-X` | 확장 속성 |
| `-H` | 하드링크 보존 |
| `-S` | sparse 파일 효율적 처리 |
| `-z` | 전송 중 압축 |
| `-zz` | 더 강한 압축 (3.2+) |
| `-v` / `-vv` | 자세히 |
| `-q` | 조용히 |
| `--progress` | 진행률 |
| `-P` | `--partial --progress` |
| `--stats` | 끝에 통계 |
| `-n`, `--dry-run` | 실제 안 보내고 시뮬레이션 |
| `--delete` | 원본에 없는 것 삭제 |
| `--delete-after` | 전송 후 삭제 |
| `--delete-excluded` | 제외된 것도 삭제 |
| `--exclude PAT` | 패턴 제외 |
| `--include PAT` | 패턴 포함 |
| `--exclude-from FILE` | 파일에서 제외 패턴 |
| `--filter 'RULE'` | 정교한 규칙 |
| `--bwlimit RATE` | 대역폭 제한 (KB/s) |
| `-e CMD` | 전송 명령 (e.g. `ssh -p 2222`) |
| `--rsh=CMD` | `-e` 와 같음 |
| `--checksum` | 시간/크기 대신 해시 비교 |
| `--update` | 더 새것만 덮어씀 |
| `--inplace` | 임시파일 없이 직접 갱신 |
| `--append-verify` | 이어 쓰기 + 해시 검증 |
| `--numeric-ids` | UID/GID 그대로 (이름 매핑 X) |
| `--chown=USER:GROUP` | 도착 후 소유자 |
| `--chmod=MODE` | 도착 후 권한 |
| `--link-dest=DIR` | 변경 없는 파일은 하드링크 (스냅샷) |
| `--backup` | 덮을 파일을 백업 |
| `--backup-dir=DIR` | 백업 저장 위치 |
| `--max-size=SIZE` | 큰 파일 제외 |
| `--min-size=SIZE` | 작은 파일 제외 |
| `--itemize-changes`, `-i` | 변경 항목 상세 |

가장 외워둘 것: **`rsync -avz --progress`** + **`--dry-run`** 으로 먼저 확인.

## 7.3 슬래시의 의미 — 가장 헷갈리는 부분

```bash
rsync -av src/  dst/    # src 의 *내용*을 dst 안으로
rsync -av src   dst/    # src *디렉토리 자체*가 dst 안에 생김
```

| 표기 | 결과 |
|------|------|
| `src/` → `dst/` | `dst/file1`, `dst/sub/file2` |
| `src` → `dst/` | `dst/src/file1`, `dst/src/sub/file2` |

`/`를 끝에 붙이는 것은 "이 디렉토리 안의 내용"을 가리킨다. 확실치 않으면 `--dry-run`.

## 7.4 SSH 위에서 rsync (가장 흔한 용법)

```bash
# 로컬 → 원격
rsync -avz src/ user@host:/dst/

# 원격 → 로컬
rsync -avz user@host:/src/ ./dst/

# 비표준 포트
rsync -avz -e "ssh -p 2222" src/ user@host:/dst/

# 키 지정
rsync -avz -e "ssh -i ~/.ssh/id_ed25519_work" src/ user@host:/dst/

# 점프 호스트
rsync -avz -e "ssh -J bastion" src/ user@internal:/dst/
```

config 별칭은 그대로 동작:

```bash
rsync -avz src/ dev:/dst/
```

## 7.5 백업 — `--delete` 의 신중함

원본에 없으면 도착에서 지운다. 미러링의 핵심.

```bash
# 도착에 새로 생긴 것까지 일치시킴
rsync -av --delete src/ dst/
```

**반드시** `--dry-run` 먼저:

```bash
rsync -avn --delete src/ dst/ | less
```

옵션 변형:

```
--delete          # 기본 (during)
--delete-before
--delete-during
--delete-after    # 다 보낸 후 (안전)
--delete-excluded # exclude된 것도 도착에서 제거
--max-delete=N    # N개 초과 삭제 시 중단 (사고 방지!)
```

`--max-delete=100` 같이 안전선을 두는 습관.

## 7.6 제외 / 필터

### --exclude / --include 단순 패턴

```bash
rsync -av \
  --exclude='*.tmp' \
  --exclude='node_modules' \
  --exclude='.git' \
  src/ dst/
```

### 파일에서

`exclude.list`:
```
*.log
*.tmp
__pycache__/
.DS_Store
node_modules/
build/
```

```bash
rsync -av --exclude-from=exclude.list src/ dst/
```

### include + exclude 조합 (까다로움)

특정 확장자만 동기화:

```bash
rsync -av \
  --include='*/' \
  --include='*.md' \
  --exclude='*' \
  src/ dst/
```

규칙: 위에서부터 매칭, **첫 매칭이 결정**. 그래서 디렉토리(`*/`)와 원하는 파일을 먼저 include 한 후 마지막에 모든 것 exclude.

### --filter 고급 규칙

```bash
rsync -av --filter=':- .gitignore' src/ dst/
# 디렉토리 트리에서 .gitignore 를 자동으로 exclude 규칙으로
```

## 7.7 진행률, 속도, 통계

```bash
rsync -avh --progress --stats src/ dst/
```

```
sending incremental file list
src/big.iso
   500.00M  56%   12.34MB/s    0:00:32 (xfr#3, to-chk=120/1234)

Total transferred file size: 1.23G
Literal data: 234.56M
Matched data: 998.99M
File list size: 1.23K
Total bytes sent: 235.00M
Total bytes received: 0.05K
sent 235.00M bytes  received 50 bytes  10.23MB/s
total size is 1.23G  speedup is 5.23
```

`speedup`이 1보다 크면 델타 전송이 효과를 본 것.

## 7.8 스냅샷 백업 — `--link-dest`

매일 풀백업처럼 보이지만, 변경 없는 파일은 하드링크라 디스크 절약.

```bash
PREV=/backup/2026-05-06
TODAY=/backup/$(date +%F)
SRC=/data/

rsync -av --delete \
  --link-dest="$PREV" \
  "$SRC" "$TODAY/"
```

각 날짜 디렉토리가 마치 풀백업처럼 보이지만, 변하지 않은 파일은 같은 inode 공유.

```bash
ls /backup/
2026-05-05  2026-05-06  2026-05-07
du -sh /backup/*    # 변경분만 실제 용량
```

`Time Machine` 류 백업 시스템의 기본 원리.

### 회전 스크립트

```bash
#!/bin/bash
set -euo pipefail
DST=/backup
SRC=/data/
TODAY=$(date +%F)
LINKDEST=$(ls -1d $DST/2* 2>/dev/null | tail -1)

mkdir -p "$DST/$TODAY"
if [ -n "$LINKDEST" ]; then
  rsync -a --delete --link-dest="$LINKDEST" "$SRC" "$DST/$TODAY/"
else
  rsync -a "$SRC" "$DST/$TODAY/"
fi

# 30일 이전은 삭제
find $DST -maxdepth 1 -type d -name '20*' -mtime +30 -exec rm -rf {} +
```

## 7.9 큰 파일 효율 — `--inplace`, `--append-verify`

```bash
# 큰 가상디스크/DB 파일: 새 임시 안 만들고 직접 수정
rsync -av --inplace --no-whole-file src/ dst/

# 끊겼다 이어받기 (해시 검증 포함)
rsync -av --append-verify big.iso host:/dst/
```

`--inplace`는 도착에서 파일이 잠시 깨진 상태가 될 수 있으니 활성 DB 파일에는 주의.

## 7.10 양방향, 원격 → 원격

rsync 자체는 단방향. 양방향은 [unison](https://www.cis.upenn.edu/~bcpierce/unison/) 같은 별도 도구 또는 두 번 실행.

원격↔원격은 직접 안 됨. 한쪽을 경유하거나 쉘로 우회:

```bash
# A 에서 B 로 (로컬 경유)
ssh A "rsync -avz src/ user@B:/dst/"

# 또는 로컬에서 한 번에
rsync -avz user@A:/src/ user@B:/dst/    # 안 됨!
# 대신 두 단계:
rsync -avz user@A:/src/ /tmp/staging/
rsync -avz /tmp/staging/ user@B:/dst/
```

## 7.11 rsync 데몬 (rsyncd)

SSH 없이 rsync 전용 서버. 빠르고 간단하지만 평문 (TLS 없음). 신뢰할 수 있는 내부망에만.

`/etc/rsyncd.conf`:

```ini
uid = nobody
gid = nogroup
use chroot = yes
max connections = 10
log file = /var/log/rsyncd.log

[backup]
    path = /srv/backup
    comment = Backup area
    read only = no
    auth users = backupuser
    secrets file = /etc/rsyncd.secrets
    hosts allow = 10.0.0.0/8
```

`/etc/rsyncd.secrets` (chmod 600):
```
backupuser:supersecret
```

서비스 시작:

```bash
sudo systemctl enable --now rsync
```

클라이언트:

```bash
RSYNC_PASSWORD=supersecret \
rsync -av src/ backupuser@host::backup/
# (쌍콜론 ::)

# 또는 URL
rsync -av src/ rsync://backupuser@host/backup/
```

## 7.12 cron 자동화

```cron
# 매일 03:00 백업
0 3 * * * /usr/local/bin/backup.sh >> /var/log/backup.log 2>&1
```

`backup.sh`:

```bash
#!/bin/bash
set -euo pipefail
exec 9>/var/run/backup.lock
flock -n 9 || exit 1     # 중복 실행 방지

LOG=/var/log/backup-$(date +%F).log
{
  rsync -avz --delete --partial --max-delete=200 \
    --exclude-from=/etc/backup.exclude \
    /data/ backup@host:/srv/backup/$(hostname)/
} >> "$LOG" 2>&1
```

`flock`으로 동시 실행 방지, `--max-delete`로 사고 방지.

## 7.13 디버깅과 진단

```bash
# 무엇이 변하는지 정확히
rsync -avni --delete src/ dst/

# 출력 의미
# >f.st...... file.txt    # f=일반파일, s=size 변경, t=time 변경
# *deleting   old.txt     # 삭제됨
# cd+++++++++ newdir/     # 새 디렉토리

# 매우 자세한 로그
rsync -avvv src/ dst/ 2> rsync.log

# 특정 파일만 시뮬레이션
rsync -avn --include='only.txt' --exclude='*' src/ dst/
```

### itemize 코드 해석

```
YXcstpoguax  path
```

- `Y`: `<` 보내는 중, `>` 받는 중, `c` 생성, `h` 하드링크, `.` 변경 없음
- `X`: `f` 파일, `d` 디렉토리, `L` 심볼릭, `D` 디바이스, `S` 소켓
- `c`: 체크섬 다름
- `s`: size 다름
- `t`: 시간 다름
- `p`: 권한 다름
- `o`: 소유자
- `g`: 그룹

## 7.14 흔한 실수와 대처

| 실수 | 결과 | 대처 |
|------|------|------|
| `src` vs `src/` 헷갈림 | 의도 다른 위치에 복사 | `--dry-run` 먼저 |
| `--delete` 무방비 사용 | 데이터 대량 삭제 | `--max-delete=N`, dry-run |
| 권한 손실 | 도착에서 권한 어긋남 | `-a` 사용 |
| 한글 파일명 깨짐 | UTF-8 미설정 환경 | `LANG=C.UTF-8 rsync ...` |
| 시계 차이 | 매번 전송 | NTP 동기화, `--checksum` |
| 매우 많은 작은 파일 느림 | inotify 제한 | `tar | ssh`도 고려 |
| 큰 트리 메모리 사용 | rsync가 파일 리스트 메모리 적재 | rsync 3+ 자동 incremental |

## 7.15 자주 쓰는 한 줄 패턴

```bash
# 미러링 (조심)
rsync -av --delete --partial src/ user@host:/dst/

# 안전 백업 (삭제 안 함)
rsync -av --partial /data/ /backup/

# 큰 파일만 빠르게
rsync -av --min-size=100M src/ dst/

# 해시 비교로 정확히
rsync -avc src/ dst/

# git 디렉토리 제외
rsync -av --exclude='.git' --exclude='node_modules' src/ dst/

# 도착에서 권한 통일
rsync -av --chown=www-data:www-data --chmod=Du=rwx,Dg=rx,Do=rx,Fu=rw,Fg=r,Fo=r \
  src/ /var/www/

# 대역폭 제한 + 압축
rsync -avz --bwlimit=2000 src/ host:/dst/

# 진행 + 통계 + dry-run
rsync -avhn --progress --stats --delete src/ dst/

# 한 번 끊어진 큰 전송 이어가기
rsync -avP big.iso host:/dst/

# 로컬 디렉토리 인덱스만 (전송 X)
rsync -avn --list-only src/

# rsync 데몬 모듈 목록
rsync host::
```

다음 챕터: [제8장]

\newpage

---


# 08. FTP 와 lftp

> 전통 FTP는 평문이라 사용 자제. 그러나 레거시 환경 대응 + 강력한 lftp 활용은 알아둘 가치.

## 8.1 FTP 기본 개념

- **포트**: 21 (제어), 데이터는 별도 (active 20, passive 임의)
- **active vs passive**: 방화벽/NAT 환경은 거의 항상 passive
- **평문**: 패스워드/데이터 모두 노출 → FTPS(FTP+TLS) 또는 SFTP 권장
- **익명 FTP**: `anonymous` / 이메일주소

## 8.2 ftp 클라이언트 (전통)

```bash
sudo apt install ftp     # 또는 inetutils-ftp
ftp host
ftp -p host              # passive 모드
ftp -n host              # 자동 로그인 안 함
```

### 인터랙티브 명령

| 명령 | 의미 |
|------|------|
| `open HOST` | 연결 |
| `user NAME` | 사용자 |
| `pass` | 패스워드 (보통 자동) |
| `pwd` / `cd` | 원격 디렉토리 |
| `lcd` | 로컬 디렉토리 |
| `ls` / `dir` | 목록 |
| `get FILE` | 다운로드 |
| `put FILE` | 업로드 |
| `mget PAT` | 다중 다운 |
| `mput PAT` | 다중 업 |
| `prompt` | 다중 전송 시 확인 토글 (off 권장) |
| `binary` / `bin` | 바이너리 모드 |
| `ascii` | 텍스트 모드 |
| `passive` | passive 토글 |
| `hash` | 해시 표시 (진행) |
| `mkdir` / `rmdir` | 디렉토리 |
| `delete FILE` | 삭제 |
| `rename SRC DST` | 이름 변경 |
| `chmod MODE FILE` | 권한 (서버 지원 시) |
| `bye` | 종료 |

### 한 번 들어가서 쓰는 흐름

```
$ ftp -p ftp.example.com
Name: anonymous
Password: me@example.com
ftp> binary
ftp> cd pub/data
ftp> prompt
Interactive mode off.
ftp> mget *.tar.gz
...
ftp> bye
```

`prompt off`를 빼먹으면 mget마다 yes/no 묻는다.

## 8.3 ASCII vs Binary

- **ASCII**: 줄바꿈을 OS 별로 변환 (CRLF↔LF). 텍스트 파일에만.
- **Binary**: 그대로. 압축, 이미지, 실행파일 → **반드시 binary**.

기본을 binary로 두는 습관이 안전.

```
ftp> binary
200 Type set to I.
```

## 8.4 보안 — FTPS / 비권장

- **FTPS**: FTP over TLS. 21 포트, AUTH TLS 명령으로 업그레이드(explicit). 또는 990 포트 implicit.
- **SFTP** (← 이게 진짜 안전한 선택): SSH 기반, 단일 포트
- **FTP**: 평문, 신뢰할 수 없는 망에선 절대 사용 금지

내부망/레거시 외 FTP를 쓸 일은 거의 없다. 새 시스템은 **무조건 SFTP**.

## 8.5 lftp — FTP/SFTP/HTTP 만능 클라이언트

`ftp`보다 압도적으로 강력. 동일 인터페이스로 FTP/SFTP/HTTP/HTTPS 모두 처리.

```bash
sudo apt install lftp

lftp ftp.example.com
lftp -u user,pw ftp.example.com
lftp -u user sftp://host
lftp http://example.com/dir/
```

URL 형태:

| URL | 프로토콜 |
|-----|----------|
| `ftp://host` | FTP |
| `ftps://host` | FTP+TLS |
| `sftp://user@host` | SFTP |
| `http://host` | HTTP |
| `https://host` | HTTPS |

### lftp 의 강점

- 미러 동기화 (`mirror`)
- 큐(queue)로 다중 전송, 일시정지
- 자동 재시도, 재개
- 스크립트 기반 자동화
- 책갈피(bookmark)
- 토큰 단위 dispatch (병렬 N개)
- 한 줄 명령으로 끝낼 수 있는 `-e`

### 기본 명령

| 명령 | 의미 |
|------|------|
| `ls` / `cls` | 목록 (cls는 컬러풀하고 빠름) |
| `cd` / `lcd` | 이동 |
| `get` / `put` / `mget` / `mput` | 전송 |
| `mirror` | 디렉토리 동기화 |
| `mirror -R` | 리버스 미러 (업로드) |
| `pget -n N FILE` | N개 병렬 다운로드 |
| `queue CMD` | 큐에 추가 |
| `queue start` | 큐 시작 |
| `bookmark add NAME` | 책갈피 |
| `bookmark list` | 책갈피 목록 |
| `set OPT VALUE` | 옵션 설정 |
| `find` | 원격 find |
| `du` | 원격 용량 |
| `glob CMD PAT` | 와일드카드 일괄 |
| `at TIME -- CMD` | 예약 실행 |
| `! CMD` | 로컬 셸 |
| `exit` | 종료 |

### mirror — lftp의 꽃

```
lftp ftp.example.com
lftp> mirror -e -P 5 --verbose /remote/data /local/data
```

| 옵션 | 의미 |
|------|------|
| `-c` | 변경된 것만 (기본) |
| `-e` | 원본에 없는 것 도착에서 삭제 (`--delete`) |
| `-n` | 새것만 |
| `-r` | 비재귀 |
| `-R` | 리버스 (로컬 → 원격) |
| `-P N` | N개 병렬 |
| `--parallel=N` | 동일 |
| `--use-pget-n=N` | 큰 파일 분할 다운로드 |
| `--include PAT` | 포함 |
| `--exclude PAT` | 제외 |
| `--exclude-glob PAT` | 글로브 제외 |
| `--newer-than DATE` | 날짜 이후만 |
| `--only-missing` | 도착에 없는 것만 |
| `--continue` | 이어받기 |
| `--dry-run` | 시뮬레이션 |
| `--log FILE` | 로그 |

### 분할 병렬 다운로드 — pget

```
lftp> pget -n 8 big.iso
```

같은 파일을 8개 스트림으로 나눠 받음. 큰 단일 파일에서 효과 큼.

## 8.6 lftp 옵션 기본값 설정

`~/.lftprc` 또는 `~/.lftp/rc`:

```
set ftp:passive-mode on
set net:max-retries 3
set net:reconnect-interval-base 5
set net:timeout 30
set xfer:clobber on
set ssl:verify-certificate yes
set ssl:ca-file /etc/ssl/certs/ca-certificates.crt
set mirror:use-pget-n 4
set cmd:fail-exit yes        # 에러 시 즉시 종료 (스크립트용)
```

## 8.7 책갈피로 빠르게

```
lftp> open ftp.example.com
lftp ftp.example.com:~> user me secret
lftp me@ftp.example.com:~> bookmark add work
lftp me@ftp.example.com:~> exit

# 다음에는
lftp work
```

`~/.lftp/bookmarks` 에 저장됨 (chmod 600 권장 — 비밀번호 포함).

## 8.8 한 줄 실행 — lftp -e

```bash
# 다운로드
lftp -e "get /pub/file.tar.gz; bye" ftp.example.com

# 미러링
lftp -e "mirror -e /remote /local; bye" -u user,pw ftp.example.com

# SFTP 미러
lftp -u user, sftp://host -e "mirror -R /local /remote; bye"
# 사용자만, 키 인증
```

`-e` 뒤 명령은 세미콜론으로 연결.

## 8.9 자주 쓰는 lftp 패턴

### 디렉토리 미러 + 삭제 + 병렬

```bash
lftp -u "$USER","$PASS" "$HOST" <<'EOF'
set ftp:ssl-allow no
set net:max-retries 5
mirror -e -P 4 --verbose /remote/data /local/data
bye
EOF
```

### 큰 파일 8병렬 + 이어받기

```bash
lftp "$URL" -e "pget -c -n 8 big.iso; bye"
```

### 새로 추가된 파일만

```bash
lftp "$URL" -e "
mirror --only-newer --include='*.csv' /remote /local
bye
"
```

### 업로드 후 검증

```bash
lftp -u user,pw ftp.example.com <<'EOF'
put report.csv -o /incoming/report.csv.tmp
mv /incoming/report.csv.tmp /incoming/report.csv
ls -l /incoming/report.csv
bye
EOF
```

## 8.10 디버그

```bash
lftp -d ftp.example.com         # debug 모드
# 또는 안에서
lftp> debug 5
lftp> ls
```

레벨 5면 모든 프로토콜 메시지가 보인다.

## 8.11 FTP 서버 (vsftpd 잠깐)

`/etc/vsftpd.conf` 핵심:

```
listen=YES
listen_ipv6=NO
anonymous_enable=NO
local_enable=YES
write_enable=YES
chroot_local_user=YES
allow_writeable_chroot=YES
pasv_enable=YES
pasv_min_port=40000
pasv_max_port=40100
ssl_enable=YES
rsa_cert_file=/etc/ssl/certs/vsftpd.pem
rsa_private_key_file=/etc/ssl/private/vsftpd.pem
force_local_data_ssl=YES
force_local_logins_ssl=YES
```

방화벽에 21, 40000-40100 (passive 범위) 개방.

> 가능하면 vsftpd 대신 SFTP 전용 사용자(이전 챕터)로 운영하라.

## 8.12 FTP vs SFTP vs lftp 사용 결정 트리

```
새 시스템 / 안전한 채널 필요?
├─ Yes → SFTP / rsync over SSH
└─ No (레거시 FTP만 있음)
   ├─ 단순 작업 → ftp 명령
   └─ 자동화 / 미러링 / 큰 파일
      → lftp (FTP / FTPS / SFTP / HTTP 모두 가능)
```

다음 챕터: [제9장]

\newpage

---


# 09. FTP 자동화

> .netrc, lftp 스크립트, expect — 무인 FTP 작업의 모든 패턴.

## 9.1 자동화 전제

| 환경 | 권장 도구 |
|------|-----------|
| 단순 다운/업 (FTP) | `lftp -e ... -u user,pw` |
| 자격증명 별도 보관 | `~/.netrc` |
| 인터랙티브 prompt 회피 | expect, lftp |
| 미러 동기화 | `lftp ... mirror` |
| 안전 채널 강제 | SFTP (이전 챕터들 참고) |
| 다중 호스트 | 셸 루프 + lftp |

핵심은 "패스워드를 어떻게 안전하게 넘길 것인가" 와 "에러를 어떻게 감지할 것인가".

## 9.2 ~/.netrc — 표준 자격증명 파일

`ftp`, `lftp`, `curl`, `wget`이 모두 읽는다.

`~/.netrc`:

```
machine ftp.example.com
login myuser
password mysecret

machine sftp.example.com
login deploy
password anothersecret

default
login anonymous
password me@example.com
```

권한 필수:

```bash
chmod 600 ~/.netrc
```

이제 패스워드 없이:

```bash
ftp ftp.example.com
lftp ftp.example.com
curl -n ftp://ftp.example.com/pub/
wget --netrc ftp://ftp.example.com/file
```

### 강점/약점

- ✅ 표준화, 여러 도구가 인식
- ✅ 코드와 자격증명 분리
- ❌ 평문. 디스크에 그대로 → 디스크 암호화 + 600 + 별도 사용자
- ❌ 호스트당 한 계정만

대안: `pass`(GPG), `gnome-keyring`, AWS Secrets Manager 등 + 환경변수로 전달.

## 9.3 lftp 자동화 — 가장 깔끔한 길

### 한 줄

```bash
lftp -e "
set ftp:passive-mode on
set net:max-retries 5
mirror -e --only-newer /remote /local
bye
" -u "$U","$P" ftp.example.com
```

### 스크립트 파일

`upload.lftp`:
```
set ftp:passive-mode on
set net:max-retries 3
set xfer:clobber on
set cmd:fail-exit yes
open ftp.example.com
user "$USER" "$PASSWORD"
cd /incoming
lcd /var/output
mput *.csv
bye
```

```bash
USER=me PASSWORD=secret lftp -f upload.lftp
```

`set cmd:fail-exit yes` 는 명령 하나라도 실패하면 lftp 자체가 즉시 비정상 종료 → 셸에서 `$?`로 감지 가능.

### .netrc 와 조합

```bash
# .netrc 에 인증 두고
lftp ftp.example.com -e "
mirror -e /remote /local
bye
"
```

별도로 `-u`를 안 줘도 lftp가 .netrc 를 읽는다.

## 9.4 ftp 명령 + heredoc

기본 `ftp` 도 자동화 가능 (단순 작업에).

```bash
ftp -inv ftp.example.com <<EOF
user $USER $PASS
binary
prompt off
cd /incoming
mput *.csv
bye
EOF
```

| 옵션 | 의미 |
|------|------|
| `-i` | mget/mput 의 prompt 끄기 |
| `-n` | 자동 로그인 안 함 (heredoc 으로 user 명시) |
| `-v` | verbose |
| `-p` | passive (BSD ftp) |

종료 코드는 빈약하다. 진짜 자동화에는 lftp가 낫다.

## 9.5 expect 로 FTP 자동화

레거시 ftp 클라이언트가 키 입력을 직접 요구할 때.

```tcl
#!/usr/bin/env expect
set timeout 30
set host [lindex $argv 0]
set user [lindex $argv 1]
set pass [lindex $argv 2]

spawn ftp $host
expect "Name*:"
send "$user\r"
expect "Password:"
send "$pass\r"
expect "ftp>"
send "binary\r"
expect "ftp>"
send "cd /incoming\r"
expect "ftp>"
send "put report.csv\r"
expect "ftp>"
send "bye\r"
expect eof
```

```bash
chmod 700 ftp-up.exp
./ftp-up.exp ftp.example.com myuser mysecret
```

(이 패턴은 [제4장] 의 expect 와 동일 원리)

## 9.6 curl 로 FTP / FTPS

curl은 의외로 강력한 FTP 클라이언트.

```bash
# 다운로드
curl -O ftp://ftp.example.com/pub/file.tar.gz
curl -u user:pass -O ftp://ftp.example.com/data/report.csv

# 업로드
curl -T report.csv -u user:pass ftp://ftp.example.com/incoming/

# 디렉토리 목록
curl -u user:pass ftp://ftp.example.com/dir/

# FTPS (explicit TLS)
curl --ftp-ssl -u user:pass ftp://host/path
curl --ftp-ssl-reqd -u user:pass ftp://host/path     # TLS 필수

# 패시브 강제 (기본은 EPSV 시도)
curl --ftp-pasv ftp://host/path

# 리스트 명령
curl ftp://host/dir/ --list-only
```

### 자격증명 분리

```bash
# .netrc 사용
curl -n ftp://host/file

# 환경변수로
curl -u "$FTP_USER:$FTP_PASS" -T file ftp://host/path
```

### 사후 명령 (퀘트 / quote)

```bash
curl -u user:pass \
  -Q "RNFR report.csv.tmp" -Q "RNTO report.csv" \
  ftp://host/incoming/
```

업로드 후 임시명을 실제명으로 rename — 원자적 배포 패턴.

```bash
curl -u user:pass -T report.csv \
  -Q "-RNFR report.csv" -Q "-RNTO old/report-$(date +%F).csv" \
  ftp://host/incoming/
# (`-`로 시작하면 사전 명령)
```

## 9.7 wget 으로 FTP 다운로드

```bash
wget ftp://ftp.example.com/pub/file
wget ftp://user:pass@ftp.example.com/pub/file        # URL 인증 (ps 노출!)
wget --user=user --password=pass ftp://host/file     # 명령행 (역시 노출)
wget --netrc ftp://host/file                         # .netrc 사용

# 재귀 미러
wget -r -np -nH --cut-dirs=1 ftp://host/pub/data/

# 이어받기
wget -c ftp://host/big.iso
```

| 옵션 | 의미 |
|------|------|
| `-c` | 이어받기 |
| `-r` | 재귀 |
| `-np` | 부모 디렉토리 안 감 |
| `-nH` | 호스트 디렉토리 안 만듦 |
| `--cut-dirs=N` | 첫 N개 디렉토리 무시 |
| `--limit-rate=R` | 대역폭 |
| `-q` | 조용히 |
| `-O FILE` | 출력 파일 |
| `-P DIR` | 저장 디렉토리 |

## 9.8 안전 패턴 — 패스워드 노출 회피

### 절대 하지 말 것

```bash
# ❌ ps 에 노출
lftp -u user,supersecret ftp.example.com
ftp user:secret@host

# ❌ 명령행 인자
curl -u me:secret ...
```

### 권장

```bash
# ✅ .netrc + chmod 600
curl -n ftp://host/...
lftp ftp.example.com

# ✅ stdin 으로 패스워드
lftp -u user, ftp.example.com <<<"pass
mirror /a /b
bye"
# (lftp 의 -u 끝에 콤마만 두면 패스워드는 다음 줄에서)

# ✅ secret-tool / pass / vault
PASS=$(pass show ftp/example) lftp -e "..." -u user,"$PASS" host
```

### 멀티유저 호스트에서

```bash
# 임시 파일에 두고 기록 후 즉시 제거
T=$(mktemp)
chmod 600 "$T"
trap 'rm -f "$T"' EXIT
echo "$PASS" > "$T"
sshpass -f "$T" ftp-something
```

## 9.9 .netrc + macroes (자동 매크로)

`.netrc`에 매크로 정의 가능 (고급, 잘 안 씀):

```
machine ftp.example.com
login me
password secret
macdef init
binary
cd /incoming
prompt off

```

빈 줄로 매크로 끝남. `ftp ftp.example.com` → 자동으로 binary 모드 + cd 실행.

## 9.10 FTP 자동화 종합 예제 — 일일 업로드 + 검증 + 알림

```bash
#!/bin/bash
# /usr/local/bin/daily-ftp.sh
set -euo pipefail

HOST=ftp.partner.com
SRC=/var/output
LOG=/var/log/daily-ftp-$(date +%F).log
DATE=$(date +%F)
FILE="report-$DATE.csv"

exec 9>/var/run/daily-ftp.lock
flock -n 9 || { echo "already running"; exit 1; }

# .netrc 에 인증, chmod 600
lftp "$HOST" <<EOF >>"$LOG" 2>&1
set cmd:fail-exit yes
set net:max-retries 5
set net:reconnect-interval-base 10
cd /incoming
lcd $SRC
put $FILE -o $FILE.tmp
mv $FILE.tmp $FILE
ls -l $FILE
bye
EOF

# 검증: 원격 크기 == 로컬 크기
LOCAL_SIZE=$(stat -c%s "$SRC/$FILE")
REMOTE_SIZE=$(curl -ns "ftp://$HOST/incoming/$FILE" -o /dev/null -w '%{size_download}\n' --range 0-0 2>/dev/null || true)
# (간단화 — 실제로는 SIZE 명령으로)

if grep -qi "fail\|error" "$LOG"; then
  mail -s "[FTP FAIL] $DATE" ops@example.com < "$LOG"
  exit 1
fi
logger "daily-ftp $DATE OK"
```

cron:
```
30 6 * * * /usr/local/bin/daily-ftp.sh
```

## 9.11 디버깅

```bash
# 무엇을 보내고 받는지
lftp -d ftp.example.com
# 안에서: debug 5

# curl
curl -v ftp://host/...

# wget
wget -d ftp://host/...

# tcpdump (호스트만 본인 일 때)
sudo tcpdump -i any -n -A 'host ftp.example.com and port 21'
```

passive/active 협상 실패가 가장 흔한 원인.

## 9.12 흔한 문제 / 대처

| 증상 | 원인 / 대처 |
|------|-------------|
| 연결은 되는데 ls/get 멈춤 | passive mode 필요. `set ftp:passive-mode on` |
| `425 Failed to establish connection` | passive 포트 범위 막힘 (방화벽) |
| TLS 협상 실패 | `set ftp:ssl-protect-data yes`, `ssl:verify-certificate no` 임시 시도 |
| 한글 파일명 깨짐 | 서버 인코딩과 lftp 의 `set file:charset` 일치 |
| 큰 파일 도중 끊김 | `mirror --continue`, `pget -c -n 4` |
| 중복 실행 | flock |
| 자격증명 노출 | .netrc 600 |
| 시간대 차 | 도착 파일 time 어긋남 → `set xfer:keep-mtime yes` |

다음 챕터: [제10장]

\newpage

---


# 10. Telnet — 디버깅의 보석, 보안의 적

> 평문 원격 셸로는 절대 쓰지 말 것. 그러나 텍스트 프로토콜 디버거로는 여전히 유용.

## 10.1 Telnet 의 두 얼굴

- ❌ **원격 셸로의 telnet**: 평문, 인증 정보 그대로 노출. SSH로 즉시 교체.
- ✅ **포트/프로토콜 진단 도구로의 telnet**: HTTP, SMTP, IMAP, POP3, Redis 등 텍스트 프로토콜 수동 확인.

`nc` (netcat) 가 더 안전한 대안이지만, telnet 은 거의 모든 시스템에 미리 깔려 있어 빠르게 손에 잡힌다.

## 10.2 설치 / 호출

```bash
sudo apt install telnet         # debian/ubuntu
sudo dnf install telnet         # rhel/fedora
sudo pacman -S inetutils        # arch (inetutils-telnet)

telnet HOST PORT
telnet 192.168.1.10 22
telnet smtp.gmail.com 587
```

기본 포트 23 (telnet 데몬)은 거의 어디에도 더 이상 열려 있지 않다. 우리가 쓰는 건 임의 포트.

## 10.3 포트 도달성 확인

가장 흔한 용법: "이 포트 열렸나?"

```bash
$ telnet google.com 80
Trying 142.250.207.78...
Connected to google.com.
Escape character is '^]'.
^]
telnet> quit
Connection closed.
```

- `Connected to ...` → 포트 열림
- `Connection refused` → 호스트는 살아있는데 포트 닫힘
- `Connection timed out` → 방화벽/네트워크/호스트 다운
- `Name or service not known` → DNS 실패

### 종료 방법

`Ctrl+]` → `quit` Enter. 이게 안 되면 또 다른 터미널에서 `pkill telnet`.

## 10.4 escape 시퀀스

기본 escape: `Ctrl+]`. 이 키를 누르면 `telnet>` 명령 모드로 전환.

| 명령 | 의미 |
|------|------|
| `quit` / `q` | 종료 |
| `close` | 연결만 끊고 telnet 유지 |
| `open HOST PORT` | 새 연결 |
| `status` | 현재 상태 |
| `set echo` | 에코 토글 |
| `mode line` | 라인 단위 (Enter로 전송) |
| `mode char` | 문자 단위 (즉시 전송) |
| `display` | 모든 옵션 |
| `?` | 도움말 |

대부분의 텍스트 프로토콜 디버깅에는 기본값이면 충분.

## 10.5 HTTP 수동 호출

```bash
$ telnet example.com 80
Trying ...
Connected to example.com.
GET / HTTP/1.1
Host: example.com
Connection: close

HTTP/1.1 200 OK
Date: ...
Content-Type: text/html
...
```

- `GET / HTTP/1.1` 입력 후 Enter
- `Host:` 헤더 (HTTP/1.1 필수) 후 Enter
- `Connection: close` 응답 후 즉시 종료
- 마지막 빈 줄(Enter 한 번 더) → 요청 끝

HEAD 만 보고 싶으면:

```
HEAD / HTTP/1.1
Host: example.com
Connection: close

```

HTTPS(443)는 telnet으로 못 함 (TLS handshake 필요). `openssl s_client -connect host:443` 사용.

## 10.6 SMTP 수동 진단

```bash
$ telnet smtp.example.com 25
Connected to smtp.example.com.
220 smtp.example.com ESMTP Postfix
EHLO me.example.com
250-smtp.example.com
250-PIPELINING
250-SIZE 10240000
250-AUTH PLAIN LOGIN
250 8BITMIME
MAIL FROM:<me@example.com>
250 2.1.0 Ok
RCPT TO:<you@example.com>
250 2.1.5 Ok
DATA
354 End data with <CR><LF>.<CR><LF>
Subject: hi

본문 한 줄
.
250 2.0.0 Ok: queued as ABCD123
QUIT
221 2.0.0 Bye
```

- `.` 한 점만 있는 줄로 메일 종료
- `EHLO` 응답에 서버가 지원하는 확장 표시
- `STARTTLS` 가 필요하면 telnet으로는 한계 → openssl

테스트가 끝났으면 `QUIT`.

## 10.7 IMAP / POP3 / FTP 제어

### POP3 (110)

```
USER me
PASS secret
LIST
RETR 1
QUIT
```

### IMAP (143)

```
a1 LOGIN me secret
a2 SELECT INBOX
a3 SEARCH ALL
a4 FETCH 1 BODY[]
a5 LOGOUT
```

각 명령 앞에 임의 태그(a1, a2...) 붙이는 게 IMAP 규칙.

### FTP (21)

FTP 자체도 텍스트 프로토콜이라 telnet으로 제어 채널 직접 조작 가능.

```
USER me
PASS secret
PWD
TYPE I
PASV
LIST
QUIT
```

데이터 채널은 별도 포트라 실제 파일 받기는 힘듦. 디버깅 용도.

## 10.8 Redis (6379) — 프로토콜 디버깅

Redis 는 RESP 라는 텍스트 친화 프로토콜이라 telnet으로도 가능.

```bash
$ telnet localhost 6379
PING
+PONG
SET hello world
+OK
GET hello
$5
world
QUIT
+OK
```

> 실무에선 `redis-cli` 가 정답이지만, "포트 살아있나?" 진단엔 telnet이 가장 빠르다.

## 10.9 nc (netcat) 로의 이행

같은 일을 `nc` 가 더 깔끔하게 한다.

```bash
nc -v google.com 80
nc -zv google.com 80          # 포트 체크만
nc -w 5 host port             # 5초 타임아웃
```

차이:

| 기능 | telnet | nc |
|------|--------|----|
| 포트 도달성 | OK | `nc -zv` 한 줄 |
| 텍스트 프로토콜 송수신 | OK | OK |
| 라인 끝 처리 | telnet 옵션 협상 영향 | 그대로 |
| TLS | ❌ | `ncat --ssl` (Nmap nc) |
| UDP | ❌ | `nc -u` |
| 스크립트 친화 | 약함 | 강함 |

자세한 nc는 [제33장].

## 10.10 telnet 이 더 적합한 순간

- **CRLF 자동 변환**: telnet은 텍스트 프로토콜에서 CRLF 처리를 잘 해 준다. nc는 옵션 필요 (`-C`).
- **에코 처리**: 일부 옵션 협상이 자동
- **즉석 진단**: 거의 모든 곳에 깔려 있음

## 10.11 자동화 — heredoc + nc 가 정답

자동화는 telnet이 옵션 협상 때문에 까다로워서 nc/lftp/curl 권장.

```bash
# HTTP HEAD 한 번 (자동화)
{
  printf 'HEAD / HTTP/1.1\r\nHost: example.com\r\nConnection: close\r\n\r\n'
  sleep 1
} | nc example.com 80

# 또는 더 깔끔히
curl -sI http://example.com
```

그래도 telnet으로 자동화하고 싶다면 expect:

```tcl
#!/usr/bin/env expect
set timeout 10
spawn telnet smtp.example.com 25
expect "220 "
send "EHLO me\r"
expect "250 "
send "QUIT\r"
expect eof
```

## 10.12 telnetd (서버) — 절대 운영 X

`telnetd` 자체가 패키지에 있지만 보안상 켜면 안 된다. 대안 비교 (의미 없지만 참고):

| 용도 | 대안 |
|------|------|
| 원격 셸 | SSH |
| 방화벽 뒤 단순 디바이스 (라우터 콘솔) | 대부분 SSH 가능, 안 되면 격리망에서만 |

## 10.13 진단 체크리스트 (포트가 안 열리는 듯할 때)

```bash
# 1. DNS
dig +short example.com

# 2. 라우팅
traceroute example.com

# 3. ICMP 도달
ping -c 3 example.com

# 4. TCP 포트
telnet example.com 443
# or
nc -zv example.com 443
# or
curl -v telnet://example.com:443    # 단순 연결만

# 5. 로컬에서 listen 중인지 (자기 서버일 때)
ss -ltn 'sport = :443'

# 6. 방화벽 (iptables)
sudo iptables -L INPUT -n -v --line-numbers | grep 443
```

각 단계에서 어디서 막히는지 보면 원인이 좁혀진다.

## 10.14 짧은 결론

- 운영용 원격 셸 telnet 사용 금지 (SSH로 교체)
- 디버깅 도구로는 여전히 빠르고 유용
- 자동화는 nc/curl/lftp 가 낫다
- 더 깊은 디버깅은 [제34장]

다음 챕터: [제11장]

\newpage

---


# 11. wget 과 curl

> wget = "파일을 가져온다", curl = "HTTP 클라이언트의 스위스 칼". 쓰임이 다르다.

## 11.1 큰 그림

| 용도 | 도구 |
|------|------|
| 단순 다운로드 한 줄 | `wget URL` |
| 디렉토리/사이트 재귀 미러 | `wget -r ...` |
| REST API 호출, 헤더/메서드/쿠키/인증 정밀 제어 | `curl` |
| 스크립트로 파이프라인 조립 | `curl` |
| 백그라운드 다운로드 | `wget -b` |
| HTTPS, FTP, FTPS, SCP, SFTP, SMTP 등 다중 프로토콜 | `curl` |

둘 다 어디에나 깔려 있다. 차이를 알고 골라 쓰자.

---

## 11.2 wget — 빠른 다운로드

### 기본

```bash
wget https://example.com/file.tar.gz       # ./file.tar.gz
wget -O out.tar.gz URL                     # 파일명 지정
wget -P /tmp URL                           # 저장 디렉토리
wget -c URL                                # 이어받기
wget -q URL                                # 조용히
wget -b URL                                # 백그라운드 (wget-log 에 진행)
wget --limit-rate=500k URL                 # 속도 제한
wget --tries=10 --waitretry=20 URL         # 재시도
wget -t 0 URL                              # 무한 재시도 (-t 0)
```

### URL 목록 일괄

`urls.txt`:
```
https://example.com/a.tar.gz
https://example.com/b.tar.gz
```

```bash
wget -i urls.txt
wget -i urls.txt -P /downloads -nc       # nc=no clobber (이미 있으면 스킵)
```

### 사이트 재귀 미러

```bash
wget --mirror --convert-links --adjust-extension --page-requisites \
     --no-parent https://example.com/docs/
```

| 옵션 | 의미 |
|------|------|
| `--mirror` | `-r -N -l inf --no-remove-listing` 묶음 |
| `-r` | 재귀 |
| `-l N` | 깊이 |
| `-np`, `--no-parent` | 부모 디렉토리로 안 감 |
| `-N` | 시간 비교 후 갱신 |
| `-k`, `--convert-links` | 로컬 보기 위해 링크 변환 |
| `-p` | 페이지 표시에 필요한 모든 리소스 |
| `-E` | .html 확장자 추가 |
| `-nH` | 호스트 디렉토리 안 만듦 |
| `--cut-dirs=N` | 첫 N개 경로 무시 |
| `-A LIST` | 받을 확장자 |
| `-R LIST` | 거부할 확장자 |
| `--reject-regex=PAT` | 정규식 거부 |
| `-D DOMAIN` | 도메인 제한 |
| `-w SEC` | 요청 사이 대기 |
| `--random-wait` | wait 의 0.5~1.5x 랜덤 |
| `-U "STRING"` | User-Agent |
| `--no-check-certificate` | TLS 검증 끄기 (위험) |

### 인증

```bash
# Basic
wget --user=me --password=secret URL
wget --http-user=me --http-password=secret URL

# .netrc 사용
wget --netrc URL

# 쿠키
wget --load-cookies cookies.txt URL
wget --save-cookies cookies.txt --keep-session-cookies URL
```

### 헤더 / 리다이렉트

```bash
wget --header="Authorization: Bearer $TOKEN" URL
wget --max-redirect=5 URL
wget --no-clobber URL          # 같은 이름이면 스킵
wget --content-disposition URL # 서버가 알려주는 파일명 사용
```

### 진행 표시

```bash
wget -q --show-progress URL    # 점만 진행
wget --progress=bar:force URL  # 막대 바
wget --progress=dot URL
```

### 대역폭/스로틀링

```bash
wget --limit-rate=200k URL
wget --bind-address=10.0.0.5 URL    # 특정 인터페이스로
```

### FTP

[제9장] 참조. wget은 FTP 다운로드도 지원하지만 FTPS는 약함 (ssl 옵션 일부).

### 스크립트 친화 종료 코드

| 코드 | 의미 |
|------|------|
| 0 | 성공 |
| 1 | 일반 오류 |
| 2 | 옵션 파싱 오류 |
| 3 | 파일 I/O 오류 |
| 4 | 네트워크 오류 |
| 5 | SSL 검증 실패 |
| 6 | 인증 실패 |
| 7 | 프로토콜 오류 |
| 8 | 서버가 오류 응답 |

스크립트:

```bash
if ! wget -q "$URL" -O "$DST"; then
  echo "download failed: $?"
  exit 1
fi
```

---

## 11.3 curl — HTTP 와 그 너머

### 기본

```bash
curl URL                              # stdout 으로
curl -O URL                           # 원본 파일명으로 저장
curl -o out URL                       # 출력 파일명 지정
curl -L URL                           # 리다이렉트 따라감
curl -s URL                           # silent
curl -sS URL                          # silent + 에러는 표시
curl -f URL                           # HTTP 4xx/5xx 시 종료 코드 22 (스크립트용)
curl -I URL                           # HEAD
curl -v URL                           # verbose (요청/응답 헤더)
curl --trace-ascii - URL              # 더 자세히 (전체 패킷)
curl -w "%{http_code}\n" -o /dev/null -s URL    # 상태코드만
```

### HTTP 메서드 / 데이터

```bash
# POST 폼
curl -d "name=alice&age=20" https://api.example.com/users

# POST JSON
curl -X POST https://api.example.com/users \
  -H "Content-Type: application/json" \
  -d '{"name":"alice","age":20}'

# 파일을 본문으로
curl -X POST -H "Content-Type: application/json" \
  -d @body.json https://api.example.com/users

# 파일 업로드 (multipart)
curl -F "file=@photo.jpg" -F "title=My Pic" https://api.example.com/upload

# PUT
curl -X PUT -d '{"v":1}' -H "Content-Type: application/json" URL

# DELETE
curl -X DELETE URL

# 임의 메서드
curl -X PATCH -d '{}' URL
```

### 헤더, 인증

```bash
# Bearer 토큰
curl -H "Authorization: Bearer $TOKEN" URL

# Basic
curl -u me:secret URL
curl -u me URL                  # 패스워드 프롬프트

# 쿠키
curl -b "session=abc" URL
curl -b cookies.txt -c cookies.txt URL    # 읽기/쓰기

# 프록시
curl -x http://proxy:3128 URL
curl --socks5 host:1080 URL

# User-Agent
curl -A "Mozilla/5.0" URL

# Referrer
curl -e "https://example.com" URL
```

### 출력 포맷팅

```bash
# 헤더 분리 저장
curl -D headers.txt -o body.html URL

# 응답 시간
curl -w "@-" -o /dev/null -s URL <<'EOF'
   namelookup: %{time_namelookup}s
       connect: %{time_connect}s
   appconnect: %{time_appconnect}s
  pretransfer: %{time_pretransfer}s
     starttransfer: %{time_starttransfer}s
        total: %{time_total}s
EOF

# 상태/크기
curl -w "code=%{http_code} size=%{size_download} time=%{time_total}\n" \
  -o /dev/null -s URL
```

### 재시도, 타임아웃

```bash
curl --retry 5 --retry-delay 3 --retry-max-time 60 URL
curl --connect-timeout 5 --max-time 30 URL
```

### TLS

```bash
# 인증서 검증 끄기 (개발만)
curl -k URL

# CA 번들 지정
curl --cacert /etc/ssl/certs/myca.pem URL

# 클라이언트 인증서
curl --cert client.crt --key client.key URL

# 특정 TLS 버전 강제
curl --tlsv1.3 URL
```

### 다운로드 가속

```bash
# 이어받기
curl -C - -O URL

# 병렬 (curl 7.66+)
curl --parallel --parallel-max 8 -O URL1 -O URL2 -O URL3

# 범위 다운로드
curl -r 0-1023 -O URL          # 첫 1KB
curl -r 1024-2047 -O URL       # 1~2KB
```

### .netrc

```bash
curl -n URL                    # ~/.netrc 사용
curl --netrc-file mynetrc URL
```

### 스크립트 종료 코드

| 코드 | 의미 |
|------|------|
| 0 | 성공 |
| 6 | 호스트 해석 실패 |
| 7 | 연결 실패 |
| 22 | HTTP 4xx/5xx (`-f` 사용 시) |
| 28 | 타임아웃 |
| 35 | TLS 핸드셰이크 실패 |
| 60 | 인증서 검증 실패 |
| 92 | HTTP/2 stream 에러 |

`-f`는 자동화에서 거의 필수.

```bash
if curl -fsS -o out.json "$URL"; then
  jq . out.json
else
  echo "fetch failed: $?"
fi
```

### config 파일

```bash
curl -K config.txt URL
```

`config.txt`:
```
-s
-L
-H "Authorization: Bearer abc"
--retry 3
```

### 자주 쓰는 한 줄

```bash
# JSON API에 POST 후 jq 로 추출
curl -fsS -X POST -H 'Content-Type: application/json' \
  -d '{"q":"linux"}' https://api/example/search | jq '.results[].title'

# 다운로드 + 진행
curl -L --progress-bar -o file.iso URL

# IP 확인
curl ifconfig.me
curl ipinfo.io/ip

# 헤더만 살펴보기
curl -I https://example.com

# HTTPS 인증서 만료일
curl -vI https://example.com 2>&1 | grep "expire date"

# 파일 동시 다운로드
curl -O URL1 -O URL2 -O URL3

# slack/discord 웹훅
curl -X POST -H 'Content-Type: application/json' \
  -d '{"text":"deploy 완료"}' "$WEBHOOK_URL"

# 패스워드 없이 sftp
curl -u user: --key ~/.ssh/id_ed25519 sftp://host/path/file -o local
```

---

## 11.4 wget vs curl 비교

| 항목 | wget | curl |
|------|------|------|
| 기본 동작 | 파일로 저장 | stdout 출력 |
| 재귀 다운로드 | ✅ 강력 | ❌ |
| 단일 파일 | ✅ | ✅ |
| HTTP 메서드 다양 | 약함 | 강함 |
| 쿠키 jar | ✅ | ✅ |
| 백그라운드 | ✅ (`-b`) | ❌ (셸 `&` 필요) |
| 진행 표시 기본 | ✅ | ✅ |
| 압축 응답 자동 해제 | 일부 | `--compressed` |
| 프로토콜 | HTTP/HTTPS/FTP | HTTP/HTTPS/FTP/FTPS/SCP/SFTP/SMTP/IMAP/POP3/...|
| 라이브러리 (libcurl) | ❌ | ✅ |
| 스크립트 종료 코드 세분화 | 보통 | 매우 자세 |

**경험칙**: 손으로 한 번 받기 → wget. API/스크립트 → curl.

## 11.5 진단 트릭

### 응답 헤더 한 번에

```bash
curl -I -L https://example.com
```

### TLS 인증서 만료

```bash
echo | openssl s_client -servername example.com -connect example.com:443 2>/dev/null \
  | openssl x509 -noout -dates
```

### HTTP/2, HTTP/3 확인

```bash
curl -I --http2 https://example.com
curl -I --http3 https://example.com    # HTTP/3 빌드된 curl 필요
```

### resolve 강제 (DNS 우회)

```bash
curl --resolve example.com:443:1.2.3.4 https://example.com
```

특정 IP로 직접 테스트, DNS는 변경 안 됨.

### tcpdump 와 같이

```bash
sudo tcpdump -i any -n 'host example.com and port 443' &
curl -I https://example.com
```

다음 챕터: [제12장]

\newpage

---


# 12. tree — 디렉토리 시각화

> 폴더 구조를 한눈에. 깊이/패턴/크기까지 다 보여준다.

## 12.1 설치

```bash
sudo apt install tree
sudo dnf install tree
sudo pacman -S tree
pkg install tree           # Termux
brew install tree          # macOS
```

## 12.2 기본 사용

```bash
tree                     # 현재 디렉토리
tree /var/log
tree -L 2                # 깊이 2까지만
tree -L 3 src/
tree -d                  # 디렉토리만
tree -f                  # 전체 경로
tree -F                  # 분류자(/, *, @ 등)
tree -i                  # 들여쓰기 트리 그리지 않음 (목록처럼)
tree -a                  # 숨김 파일 포함
tree --noreport          # 끝의 "N directories, M files" 안 보임
```

출력 예:

```
.
├── src
│   ├── main.c
│   └── util.c
├── README.md
└── tests
    └── test_main.c
```

## 12.3 옵션 정리

| 옵션 | 의미 |
|------|------|
| `-L N` | 최대 깊이 |
| `-d` | 디렉토리만 |
| `-f` | 전체 경로 |
| `-i` | 들여쓰기 트리 끔 |
| `-a` | 숨김 포함 |
| `-h` | human readable size (`-s` 와 함께) |
| `-s` | 파일 크기 표시 |
| `-D` | 마지막 수정 시간 |
| `-p` | 권한 표시 |
| `-u` | 소유자 |
| `-g` | 그룹 |
| `--du` | 디렉토리 누적 크기 |
| `--inodes` | inode 번호 |
| `--device` | 디바이스 ID |
| `-P PAT` | 패턴에 맞는 파일만 (디렉토리는 그대로) |
| `-I PAT` | 패턴 제외 |
| `--matchdirs` | 패턴에 디렉토리도 |
| `--prune` | 빈 디렉토리 가지 치기 |
| `--noreport` | 요약 끔 |
| `-C` | 컬러 강제 |
| `-n` | 컬러 끔 |
| `-J` | JSON 출력 |
| `-X` | XML 출력 |
| `-H DIR` | HTML 출력 |
| `-o FILE` | 출력 파일 |
| `--filelimit N` | 파일 N개 넘는 디렉토리 생략 |
| `--charset=ascii` | ASCII 박스 문자 (구식 단말) |
| `--dirsfirst` | 디렉토리 먼저 |
| `-r` | 역순 정렬 |
| `-t` | mtime 정렬 |
| `-c` | ctime 정렬 |
| `-U` | 정렬 안 함 |
| `--sort=KEY` | name/size/mtime 등 |

## 12.4 패턴 필터

```bash
# 마크다운만
tree -P '*.md'

# 두 종류
tree -P '*.md|*.txt'

# 마크다운만 + 빈 디렉토리 제거
tree -P '*.md' --prune

# node_modules 와 .git 제외
tree -I 'node_modules|.git'

# 빌드 산출물 제외
tree -I 'build|dist|*.o|*.a'
```

`-P`는 파일 매칭이고 디렉토리는 항상 보인다 (탐색 위해). `--prune`로 매칭 결과 없는 디렉토리 제거.

## 12.5 크기와 메타데이터

```bash
# 파일 크기 + 사람 읽기 쉬운 단위
tree -sh

# 디렉토리 누적 크기
tree -h --du

# 권한 + 소유자/그룹 + 크기 + mtime
tree -pugDh

# 가장 큰 디렉토리부터
tree -h --du --sort=size -r
```

`du -sh`를 시각화한 느낌으로 디스크 정리에 유용.

```
.
├── [4.0K]  src
│   ├── [ 12K]  main.c
│   └── [3.4K]  util.c
└── [ 56K]  data
    └── [ 56K]  big.bin
```

## 12.6 정렬

```bash
tree -t           # 최신부터 (mtime)
tree -tr          # 오래된 것부터
tree --dirsfirst  # 디렉토리 → 파일
tree --sort=size -r
```

## 12.7 출력 포맷

### HTML (보고서/공유용)

```bash
tree -H "https://example.com/files" -o files.html /var/www/files
firefox files.html
```

`-H` 인자는 링크의 base URL.

### JSON (스크립트로 처리)

```bash
tree -J -L 2 | jq '.[0].contents[].name'
```

### XML

```bash
tree -X -L 2
```

### 일반 텍스트 파일로 저장

```bash
tree -L 3 > structure.txt
# ASCII 박스로 저장하려면
tree --charset=ascii -L 3 > structure.txt
```

## 12.8 큰 트리 다루기

### 깊이 제한 + filelimit

```bash
tree -L 3 --filelimit 50 .
```

50개 넘는 파일이 있는 디렉토리는 `[N entries exceeds filelimit, not opening dir]`.

### 디렉토리만

```bash
tree -d -L 3
```

### 빈 디렉토리 제거

```bash
tree --prune
```

### 매우 큰 트리: 페이저로

```bash
tree -L 4 | less -R       # -R 로 컬러 보존
```

## 12.9 옵시디언/문서 활용

### 마크다운 트리 (코드블록 안)

```bash
tree -L 2 -I 'node_modules|.git' --noreport
```

위 결과를 ` ```text ... ``` `로 감싸 문서에 붙여넣으면 깔끔.

### vault 구조 보고서

```bash
cd ~/Documents/chobocho_box
tree -L 2 -d --noreport
```

## 12.10 Termux 특이사항

```bash
pkg install tree
tree -L 2 ~/storage/shared/Documents/chobocho_box
tree -L 1 /storage/emulated/0/Documents/
```

권한 문제 시 `termux-setup-storage` 후 `~/storage` 심볼릭 링크 사용.

## 12.11 tree 가 없을 때 대체

```bash
# find 로 비슷하게
find . -type d | sort | sed -e "s|[^/]*/|│   |g" -e "s|│   \([^│]\)|├── \1|"

# Python (어디나 있음)
python3 -c "
import os, sys
def t(d='.', p=''):
  e=sorted(os.listdir(d))
  for i,f in enumerate(e):
    last=i==len(e)-1
    print(p+('└── ' if last else '├── ')+f)
    fp=os.path.join(d,f)
    if os.path.isdir(fp):
      t(fp, p+('    ' if last else '│   '))
t(sys.argv[1] if len(sys.argv)>1 else '.')
"
```

## 12.12 자주 쓰는 한 줄 모음

```bash
# 파일 개수 빠르게 (보고서 줄에서)
tree . | tail -1
# → "12 directories, 234 files"

# git 빼고 전체 구조
tree -I '.git'

# 코드만 (cf. C 프로젝트)
tree -P '*.c|*.h|*.mk|Makefile'

# 1MB 이상만 보기 (find 와 결합)
tree -sh -L 3 | grep -E "[0-9]+M"

# 가장 큰 디렉토리 10개
tree -h --du --noreport -L 1 | sort -hr -k1 | head

# 보고서 묶음
tree -aL 3 -I '.git|node_modules' \
     --du -h \
     --dirsfirst \
     -o project-structure.txt
```

다음 챕터: [제13장]

\newpage

---


# 13. Midnight Commander (mc)

> 두 패널 + 단축키. 30년 된 텍스트 모드 파일 매니저의 끝판왕.

## 13.1 mc 가 좋은 이유

- **두 패널** 구조 → 복사/이동이 직관적
- 모든 SSH/SFTP/FTP/Tar/RPM/ZIP 가상 파일시스템 (VFS)
- 내장 에디터(`mcedit`), 뷰어(`mcview`)
- 단축키 한 손으로 거의 모든 일
- 마우스도 지원

## 13.2 설치

```bash
sudo apt install mc
sudo dnf install mc
sudo pacman -S mc
pkg install mc           # Termux
```

실행:

```bash
mc
mc -b              # 흑백 (단색 단말)
mc -c              # 강제 컬러
mc -x              # 마우스 끄기
mc -d              # 마우스 켜기
mc -t              # 단순 컬러
mc DIR1 DIR2       # 좌/우 패널 시작 디렉토리
```

## 13.3 화면 구성

```
┌─ Left ─────────┐┌─ Right ─────────┐
│ 좌 패널        ││ 우 패널         │
│ 파일 목록      ││ 파일 목록       │
│                ││                 │
└────────────────┘└─────────────────┘
Hint:
[명령행]
1Help 2Menu 3View 4Edit 5Copy 6Ren 7Mkdir 8Del 9Menu 10Quit
```

상단: 메뉴(F9) / 좌/우 패널 / 명령행 / 기능키.

## 13.4 핵심 단축키

| 키 | 동작 |
|----|------|
| `Tab` | 패널 전환 |
| `Enter` | 진입 / 실행 |
| `Insert` 또는 `Ctrl+T` | 선택 토글 |
| `+` | 패턴 선택 (e.g. `*.md`) |
| `-` | 패턴 선택 해제 |
| `*` | 선택 반전 |
| `F1` | 도움말 |
| `F2` | 사용자 메뉴 |
| `F3` | 보기 (mcview) |
| `F4` | 편집 (mcedit) |
| `F5` | **복사** (다른 패널로) |
| `F6` | **이동** / 이름 변경 |
| `F7` | 디렉토리 생성 |
| `F8` 또는 `Delete` | 삭제 |
| `F9` | 상단 메뉴 |
| `F10` 또는 `Esc Esc` | 종료 |
| `Ctrl+R` | 패널 새로고침 |
| `Ctrl+\` | 즐겨찾기 디렉토리 |
| `Alt+H` | 디렉토리 히스토리 |
| `Alt+S` | 빠른 검색 (현재 패널 안에서 타이핑) |
| `Alt+?` | find file (전체 검색) |
| `Alt+C` | 디렉토리 빠른 이동 (cd) |
| `Alt+T` | 패널 보기 모드 토글 (long/brief 등) |
| `Alt+O` | 다른 패널을 같은 디렉토리로 |
| `Alt+I` | 다른 패널에서 현재 선택 디렉토리로 cd |
| `Alt+,` | 패널 위/아래 ↔ 좌/우 토글 |
| `Ctrl+O` | 패널 숨기기 ↔ 셸 |
| `Ctrl+X !` | 외부 패널 (커맨드 결과를 패널에) |
| `Ctrl+X t` | 선택 파일명을 명령행에 |
| `Ctrl+X p` | 현재 디렉토리 명령행에 |
| `Ctrl+X Ctrl+P` | 다른 패널 디렉토리 명령행에 |
| `Ctrl+Space` | 현재 디렉토리 크기 |

`Alt`가 안 먹는 단말이면 `Esc` 키를 대신 누른 후 다른 키.

## 13.5 자주 쓰는 흐름

### 두 디렉토리 동기화 (간단)

1. 좌 패널: `Alt+C` → `~/work`
2. 우 패널: `Tab`, `Alt+C` → `/mnt/usb/work`
3. 좌 패널에서 파일 선택 (`Insert` 또는 `+ *.md`)
4. `F5` → 우측으로 복사

### 원격 SFTP 패널

`F9 → Left → SFTP link...` 또는 디렉토리 입력란에:

```
sh://user@host:port/remote/path
```

마치 로컬 디렉토리처럼 SFTP 트리가 한쪽 패널에. F5로 다른 패널과 복사.

```
sh://seunghwa@dev.example.com:2222/var/www
```

(VFS는 `sh://` SFTP 외에 `ftp://`, `tar://`, `rpm://`, `zip://` 등 다양)

### 압축 파일 진입

`.tar.gz` 위에서 `Enter` → 패널이 그 안으로 들어간다 (마치 디렉토리). 안에서 파일 꺼내거나 추가 가능. `..` 로 빠져나옴.

## 13.6 보기 / 편집

### F3 보기 (mcview)

- 텍스트/바이너리 자동 감지
- `F2` hex 모드
- `F4` ASCII 모드
- `/` 검색
- `n` 다음 결과
- `Ctrl+F` 다음 파일 (선택된 여러 파일 순회)

### F4 편집 (mcedit)

| 키 | 의미 |
|----|------|
| `F2` | 저장 |
| `F3` | 마크 시작 |
| `F5` | 복사 |
| `F6` | 이동 |
| `F7` | 검색 |
| `F8` | 삭제 |
| `F9` | 메뉴 |
| `F10` | 종료 |
| `Ctrl+S` | 저장 |
| `Ctrl+F` | 검색 |
| `Ctrl+R` | 치환 |
| `Ctrl+U` | undo |

vi/emacs 안 쓰는 사람에게 무난한 에디터.

### `mcedit` 단독 실행

```bash
mcedit /etc/hosts
```

## 13.7 메뉴 (F9)

- **Left/Right**: 패널 모드, 정렬, 필터, 원격 연결
- **File**: 복사/이동/링크/속성/소유자
- **Command**: find, compare, swap panels, edit menu, edit extension file
- **Options**: 환경설정 (자동 저장)

자주 쓰는 옵션:

- `Options → Configuration` → "Auto save setup"
- `Options → Panel options` → 정렬 기본
- `Command → Edit user menu` → `~/.config/mc/menu` 사용자 메뉴

## 13.8 사용자 메뉴 (F2)

`~/.config/mc/menu`:

```
+ ! t t
g       Make this directory a git repo
        git init

+ ! t t
b       Backup selected files to /tmp
        cp -a %s /tmp/

+ t t
T       Tar selected files
        tar czf selected-$(date +%F).tgz %s

+ t t
P       Push to remote (rsync)
        rsync -av %s host:/dst/
```

`%s`: 선택된 파일들. `%f`: 현재 파일. 첫 줄의 `+`는 조건, 두 번째 글자는 단축키.

## 13.9 외부 처리 (콘텐츠 매핑)

`F9 → Command → Edit extension file` 또는 `~/.config/mc/mc.ext.ini`:

```
[markdown]
Regex=\.md$
View=glow %f
Open=mcedit %f
```

`.md` 위에서 F3는 glow로 렌더, Enter는 mcedit으로 편집.

## 13.10 find file (Alt+?)

```
Find File
Start at:  /home/user
Filename:  *.md
Content:   TODO
```

파일명 + 내용 검색을 GUI 다이얼로그로. 결과 화면에서:

- `Enter`: 그 파일로 점프
- `View`: 즉시 보기
- `Edit`: 편집
- `Panelize`: 결과를 가상 패널로

## 13.11 Panelize — 명령 결과를 패널처럼

```
F9 → Command → External panelize
Command: find . -name '*.log' -mtime -1
```

→ 어제 변경된 .log 파일들이 패널 가득. `Insert`로 선택 → F5/F6/F8.

내장 단축키:

```
Ctrl+X !
```

## 13.12 mc 테마 / 설정 위치

- `~/.config/mc/ini` — 메인 설정
- `~/.config/mc/panels.ini` — 패널 상태
- `~/.config/mc/hotlist` — 디렉토리 즐겨찾기
- `~/.config/mc/history` — 명령행/검색 히스토리
- `~/.local/share/mc/` — 숨김 캐시

테마:

```bash
mc -S dark        # 어두운
mc -S xoria256    # 256색
```

`F9 → Options → Appearance` 에서 GUI로 변경 후 자동 저장.

## 13.13 Termux 특이사항

```bash
pkg install mc
mc                  # 기본 동작
# 외부 저장소 빠른 진입
mc ~/storage/shared/Documents
```

스마트폰 키보드는 Alt 입력이 어려우니 마우스 또는 Esc 두 번 활용.

## 13.14 SSH 위에서 mc

서버에 mc만 깔면 굉장히 강력:

```bash
ssh user@host
host:~$ mc
```

`sh://other-host/...` 로 다른 서버 패널 띄우면 두 원격 서버 사이 직접 복사 가능 (mc가 중계).

## 13.15 자주 쓰는 한 줄 트릭

```bash
# 패널을 swap (Tab 으로 못 갈 때)
Ctrl+U

# 마우스 일시 비활성 (마우스 텍스트 선택)
Shift + 드래그   # 단말이 mc 마우스 가로채는 걸 우회

# 명령행에 현재 선택 파일 채우기
Ctrl+X t

# 다른 패널과 비교
F9 → Command → Compare directories

# 즉석 셸
Ctrl+O
# 다시 mc
Ctrl+O
```

## 13.16 mc 가 부담스러우면

- **ranger** — vim 키 기반 단일 패널 + 미리보기
- **nnn** — 매우 가볍고 빠름
- **lf** — go 로 다시 쓴 ranger 류
- **vifm** — vim 키 두 패널

mc 는 키 어렵지 않고 어디서나 동작 → 일단 손에 익히면 평생 우려먹는다.

다음 챕터: [제14장]

\newpage

---


# 14. find 와 xargs

> 파일을 찾고, 대량으로 처리한다. 시스템 운영의 절반은 이 둘이 한다.

## 14.1 find 기본 구조

```
find [경로...] [조건...] [동작]
```

조건과 동작은 **순서대로** 평가된다. 순서가 의미를 갖는다.

```bash
find .                              # 모든 파일/디렉토리
find /var/log -name '*.log'         # 이름 매칭
find . -type f                      # 파일만
find . -type d                      # 디렉토리만
find . -mtime -1                    # 24시간 이내 수정
find . -size +100M                  # 100MB 초과
find . -user seunghwa               # 소유자
```

## 14.2 자주 쓰는 조건

| 조건 | 의미 |
|------|------|
| `-name PAT` | 파일명 (셸 글로브) |
| `-iname PAT` | 대소문자 무시 |
| `-path PAT` | 경로 전체 매칭 |
| `-regex PAT` | 정규식 (전체 경로) |
| `-type T` | f(파일), d(디렉토리), l(링크), s(소켓), b(블록), c(문자), p(파이프) |
| `-empty` | 빈 파일/디렉토리 |
| `-size N[cwbkMG]` | 크기 (c=byte, k=KB, M=MB) |
| `-mtime N` | N일 전 수정 (-N=N일 이내, +N=N일 이전) |
| `-mmin N` | 분 단위 |
| `-atime` / `-ctime` | 접근/inode 변경 |
| `-newer FILE` | FILE 보다 새것 |
| `-user NAME` / `-uid N` | 소유자 |
| `-group NAME` / `-gid N` | 그룹 |
| `-perm MODE` | 권한 |
| `-perm /MODE` | MODE 비트 중 하나 |
| `-perm -MODE` | MODE 비트 모두 포함 |
| `-readable` / `-writable` / `-executable` | 현재 사용자 기준 |
| `-maxdepth N` | 깊이 제한 |
| `-mindepth N` | 최소 깊이 |
| `-not COND` 또는 `! COND` | 부정 |
| `-and` 또는 공백 | 논리곱 |
| `-or` | 논리합 |
| `( ... )` | 그룹 (셸 이스케이프 `\( \)` 또는 `'(' ')'`) |

## 14.3 동작

| 동작 | 의미 |
|------|------|
| `-print` | 출력 (기본) |
| `-print0` | NUL 구분 (xargs -0 와 짝) |
| `-ls` | ls -l 형식 |
| `-delete` | 즉시 삭제 |
| `-quit` | 첫 매칭에서 종료 |
| `-prune` | 디렉토리 안 들어감 |
| `-exec CMD {} \;` | 매 매칭마다 실행 |
| `-exec CMD {} +` | 한 번에 묶어 실행 (xargs 와 비슷) |
| `-execdir CMD {} \;` | 해당 파일 디렉토리에서 실행 |
| `-okdir`, `-ok` | 실행 전 확인 프롬프트 |

## 14.4 깊이와 prune

```bash
# 현재 디렉토리만
find . -maxdepth 1 -type f

# 2단계까지
find . -maxdepth 2 -type f

# .git 안에는 안 들어감
find . -path '*/.git' -prune -o -type f -print

# 다중 prune
find . \( -path '*/.git' -o -path '*/node_modules' \) -prune \
       -o -type f -name '*.js' -print
```

`-prune`은 그 디렉토리 자체는 매칭하지만 그 아래로 내려가지 않게 한다. `-o -print`로 나머지를 출력.

## 14.5 시간 / 크기 패턴

```bash
# 7일 이전 .log 삭제
find /var/log -type f -name '*.log' -mtime +7 -delete

# 24시간 이내 변경된 파일
find . -type f -mmin -1440

# 사이즈 1G 초과
find / -type f -size +1G 2>/dev/null

# 빈 디렉토리
find . -type d -empty

# 빈 파일 삭제
find . -type f -empty -delete

# 어떤 파일보다 새것
find . -newer /tmp/marker -type f
```

## 14.6 권한 검색

```bash
# world-writable 파일 (보안 점검)
find / -type f -perm -o=w 2>/dev/null

# 정확히 644
find . -type f -perm 644

# setuid 가진 것
find / -perm /4000 -type f 2>/dev/null
find / -perm -4000 -type f 2>/dev/null

# 내가 쓸 수 있는 것
find /etc -writable
```

## 14.7 -exec 의 두 가지 종결자

```bash
# 매 파일마다 cmd 호출 (느림)
find . -name '*.tmp' -exec rm {} \;

# 묶어서 한 번 호출 (xargs 와 비슷)
find . -name '*.tmp' -exec rm {} +
```

`{}`는 파일명 자리. `\;`는 매번 실행, `+`는 묶어 실행. 가능하면 `+`가 빠르다.

```bash
# 여러 인자 위치
find . -name '*.bak' -exec mv {} {}.old \;
# {}+ 는 위치 지정 안 됨 → \;를 써야 함

# execdir: 그 파일이 있는 디렉토리에서 실행
find . -name 'CMakeLists.txt' -execdir cmake . \;
```

## 14.8 find + xargs

큰 결과는 xargs로 병렬/일괄 처리.

```bash
find . -name '*.log' -print0 | xargs -0 gzip
find . -name '*.tmp' -print0 | xargs -0 rm
find . -name '*.md' -print0 | xargs -0 wc -l
```

`-print0` ↔ `-0`: NUL 구분 → 공백/한글/개행 들어간 파일명에도 안전.

## 14.9 자주 쓰는 한 줄

```bash
# 가장 큰 파일 10개
find . -type f -printf '%s %p\n' 2>/dev/null | sort -nr | head

# 가장 최근 변경 파일 10개
find . -type f -printf '%T@ %p\n' 2>/dev/null | sort -nr | head

# 디렉토리별 파일 수
find . -type f | sed 's|/[^/]*$||' | sort | uniq -c | sort -rn | head

# 권한 일괄 정리
find /var/www -type d -exec chmod 755 {} +
find /var/www -type f -exec chmod 644 {} +

# 사용자/그룹 일괄
find /var/www -exec chown www-data:www-data {} +

# 7일 이전 로그 압축
find /var/log -type f -name '*.log' -mtime +7 -exec gzip {} +

# 특정 패키지가 만든 파일 찾기 (rpm)
rpm -ql nginx | xargs -I{} find {} -type f 2>/dev/null

# 빈 파일/디렉토리 둘 다 정리
find . -empty -delete

# .DS_Store / Thumbs.db 정리
find . \( -name '.DS_Store' -o -name 'Thumbs.db' \) -delete

# 한 번도 접근 안 한 파일
find /home -atime +180 -type f
```

## 14.10 -printf 포맷

| 토큰 | 의미 |
|------|------|
| `%p` | 전체 경로 |
| `%f` | 파일명 |
| `%h` | 디렉토리 |
| `%s` | 바이트 |
| `%T@` | epoch 수정 시간 |
| `%TY-%Tm-%Td %TH:%TM` | 날짜시간 |
| `%u` `%g` | 소유자/그룹 |
| `%m` | 권한 (8진) |
| `%y` | 타입 (f, d, l...) |
| `%i` | inode |
| `%n` | 하드링크 개수 |
| `%P` | 시작 경로 제외 |

```bash
find . -type f -printf '%s\t%TY-%Tm-%Td\t%p\n' | sort -rn
```

## 14.11 find 결과를 패키지로

```bash
# 변경된 .conf 만 tar 로
find /etc -name '*.conf' -mtime -7 -print0 | tar --null --files-from=- -czf etc-changes.tgz
```

## 14.12 함정

| 함정 | 대처 |
|------|------|
| 파일명에 공백/줄바꿈 | `-print0 \| xargs -0`, `-exec ... +` |
| `-name '*.foo'`이 0 매칭 | 셸 글로브 확장 안 되도록 따옴표 |
| `-delete`가 디렉토리는 비어야 동작 | `-depth -delete` 함께 |
| `-prune` 효과 없음 | `-print` 빠뜨림. `-o -print` 명시 |
| `find /` 가 procfs 끝없이 | `-xdev` 로 한 파일시스템만 |

```bash
# 여러 mount 안 넘어감
find / -xdev -name '*.log'
```

---

## 14.13 xargs

stdin 의 항목을 인자로 명령에 넘긴다. 파이프와 짝.

```bash
echo "a b c" | xargs echo
# → a b c (한 번에)

ls *.log | xargs gzip
```

### 자주 쓰는 옵션

| 옵션 | 의미 |
|------|------|
| `-0` | NUL 구분 (find -print0 와 짝) |
| `-d DELIM` | 구분자 지정 |
| `-n N` | N개씩 묶어 실행 |
| `-L N` | N줄 마다 |
| `-I PLACE` | 자리표시자 (e.g. `-I {}`) |
| `-P N` | 병렬 N개 |
| `-r` 또는 `--no-run-if-empty` | 입력 없으면 실행 안 함 |
| `-t` | 실행할 명령 표시 |
| `-p` | 매번 yes/no 확인 |
| `-a FILE` | 파일에서 입력 |
| `-s SIZE` | 명령행 길이 제한 |
| `-x` | 길이 초과 시 즉시 종료 |
| `-E STR` | EOF 마커 |

### 핵심 패턴

```bash
# 단순
ls *.log | xargs gzip

# NUL 구분 (안전)
find . -name '*.log' -print0 | xargs -0 gzip

# {} 자리 지정
ls *.bak | xargs -I {} mv {} {}.old

# 한 번에 한 개씩
ls *.png | xargs -n1 -I{} convert {} {}.thumb.jpg

# 병렬 4개
find . -name '*.jpg' -print0 | xargs -0 -P4 -n1 jpegoptim

# 빈 입력 무시
seq 0 0 | xargs -r echo "fired"     # 출력 없음
```

### -I 와 다중 인자

```bash
cat hosts.txt | xargs -I{} ssh {} "uptime"
cat hosts.txt | xargs -I{} -P8 ssh {} "uptime"
```

`-I{}` 는 자동으로 `-L 1` 적용 → 한 줄씩.

### -t 로 실제 명령 미리 보기

```bash
find . -name '*.tmp' -print0 | xargs -0 -t rm
# rm ./a.tmp ./b.tmp ./c.tmp
```

`-p` 를 쓰면 매번 confirm.

### 셸 명령 전체를 xargs로

```bash
cat hosts.txt | xargs -I{} -P4 sh -c '
  echo "=== {} ==="
  ssh {} "uptime"
' _ {}
```

`sh -c` 안에서는 `{}` 를 그대로 변수처럼 쓰지 말고, `-c '... "$1" ...' _ {}` 로 안전하게 전달하는 패턴.

```bash
cat hosts.txt | xargs -I{} -P4 sh -c '
  h="$1"
  echo "=== $h ==="
  ssh "$h" "uptime"
' _ {}
```

## 14.14 find vs grep -r vs fd

| 도구 | 용도 |
|------|------|
| `find` | 메타데이터 + 트리 탐색 + 일괄 처리 |
| `grep -r` | 내용 검색 (이 책에선 제외 대상) |
| `fd` | find 의 빠르고 간결한 대체 (rust) |

`fd`는 자주 쓰면 좋다 (이 핸드북 범위 외이지만 추천). `.gitignore`을 자동 무시하고 기본 출력이 깔끔.

## 14.15 자주 쓰는 종합 한 줄

```bash
# 7일 이전 로그 정리 + 디스크 절약
find /var/log -type f -name '*.log' -mtime +7 -print0 | xargs -0 -r gzip
find /var/log -type f -name '*.gz'  -mtime +30 -delete

# 모든 .git 제외하고 코드 라인 수 합계
find . -type d -name '.git' -prune -o -type f \
  \( -name '*.c' -o -name '*.py' -o -name '*.go' \) -print0 \
  | xargs -0 wc -l | tail -1

# 권한 사고 회복
find /var/www -type d -exec chmod 755 {} +
find /var/www -type f -exec chmod 644 {} +

# 24시간 새 파일 모음
find . -type f -mmin -1440 -print0 | xargs -0 ls -lt | head

# 디렉토리별 사이즈 큰 순
find . -maxdepth 1 -type d -exec du -sh {} + 2>/dev/null | sort -hr
```

다음 챕터: [제15장]

\newpage

---


# 15. 압축과 아카이브 — tar, gzip, bzip2, xz, zip, 7z

> tar 는 아카이브 (묶음). gzip/bzip2/xz/zstd 는 압축. 둘은 별개.

## 15.1 큰 그림

| 형식 | 확장자 | 도구 | 특징 |
|------|--------|------|------|
| tar | .tar | tar | 아카이브만 (압축 X) |
| tar.gz / tgz | .tar.gz, .tgz | tar + gzip | 빠르고 호환성 좋음 |
| tar.bz2 / tbz2 | .tar.bz2 | tar + bzip2 | 더 작지만 느림 |
| tar.xz / txz | .tar.xz | tar + xz | 가장 작지만 가장 느림 |
| tar.zst | .tar.zst | tar + zstd | 빠르고 작음 (현대 권장) |
| zip | .zip | zip/unzip | 윈도 호환, 파일별 압축 |
| 7z | .7z | 7z, p7zip | 매우 높은 압축률 |
| rar | .rar | unrar | 읽기만 무료, 잘 안 씀 |

**유닉스 표준은 tar.gz 또는 tar.xz**. 파일 하나당 압축이 아니라 묶고 통째로 압축 → 유사 파일이 많을수록 비율 좋음.

## 15.2 tar 옵션 정리

| 옵션 | 의미 |
|------|------|
| `-c` | create (만들기) |
| `-x` | extract (풀기) |
| `-t` | list (목차) |
| `-r` | append (이어 붙이기, .tar 만) |
| `-u` | update (있으면 새것만) |
| `-f FILE` | 파일 지정 (또는 `-` stdin/stdout) |
| `-v` | verbose |
| `-z` | gzip |
| `-j` | bzip2 |
| `-J` | xz |
| `--zstd` | zstd |
| `-a` | 자동 (확장자 보고 결정) |
| `-C DIR` | 작업 디렉토리 변경 |
| `-T FILE` | 파일 목록을 파일에서 |
| `--null` | 파일 목록 NUL 구분 |
| `-X FILE` | 제외 패턴 파일 |
| `--exclude=PAT` | 제외 |
| `--include=PAT` | 포함 |
| `--strip-components=N` | 풀 때 첫 N 디렉토리 벗김 |
| `-p` | 권한 보존 |
| `--numeric-owner` | UID/GID 그대로 |
| `--xattrs` | 확장 속성 |
| `--acls` | ACL |
| `--no-recursion` | 재귀 안 함 |
| `--checkpoint=N` | N 항목마다 진행 표시 |
| `--checkpoint-action=dot` | 점으로 진행 |

옵션은 `-czvf` 처럼 묶어 쓰는 게 관례.

## 15.3 만들기 / 풀기

### 만들기

```bash
tar -czf archive.tgz dir/
tar -czvf archive.tgz dir1/ dir2/ file
tar -cJf archive.txz dir/                  # xz
tar -cjf archive.tbz2 dir/                 # bzip2
tar --zstd -cf archive.tar.zst dir/        # zstd
tar -caf archive.tar.gz dir/               # 자동 (확장자 따라)
```

### 풀기

```bash
tar -xzf archive.tgz                       # 현재 디렉토리에
tar -xzf archive.tgz -C /opt/              # 지정 위치에
tar -xJf archive.txz
tar -xaf archive.???                       # 자동 감지
tar --zstd -xf archive.tar.zst
```

### 보기 (풀지 않고)

```bash
tar -tzf archive.tgz | head
tar -tvf archive.tar    # 권한/크기/시간 포함
```

## 15.4 자주 쓰는 패턴

### 디렉토리 통째로 + 권한 보존

```bash
sudo tar -czpf /backup/etc-$(date +%F).tgz -C / etc
```

`-C /`로 부모로 이동 → 아카이브 안에 `etc/...` (절대경로 X).

### 풀 때 권한/소유자 그대로

```bash
sudo tar -xpf archive.tar --numeric-owner -C /
```

### 일부만 풀기

```bash
tar -xzf archive.tgz path/to/file
tar -xzf archive.tgz --wildcards '*.conf'
```

### strip — 깊은 디렉토리 평탄화

`archive.tgz` 안이 `project-1.2.3/src/main.c` 인데 `src/main.c` 만 원할 때:

```bash
tar -xzf archive.tgz --strip-components=1
```

## 15.5 제외 / 포함

```bash
tar -czf src.tgz --exclude='*.tmp' --exclude='node_modules' --exclude='.git' src/

# 파일에서 제외 패턴
cat > exclude.list <<EOF
*.log
*.tmp
__pycache__
.cache/
EOF
tar -czf project.tgz -X exclude.list project/
```

git 디렉토리 자동 무시:

```bash
tar --exclude-vcs -czf project.tgz project/
tar --exclude-vcs-ignores -czf project.tgz project/   # .gitignore 까지
```

## 15.6 stdin/stdout 연동

```bash
# tar 결과를 ssh 로 흘려 다른 호스트에
tar czf - dir/ | ssh host "tar xzf - -C /dst/"

# 받기
ssh host "tar czf - /var/log" | tar xzf - -C ./backup/

# tar 안에 단일 파일 어딘가에 박기
tar czf - file1 file2 | base64 > package.b64
```

이 패턴이 scp 보다 빠를 때가 많다 (작은 파일 多 → tar 가 한 번에 전송).

## 15.7 큰 아카이브 — 분할 / 진행

### 분할 (split)

```bash
tar czf - dir/ | split -b 1G - archive.tgz.part-
# archive.tgz.part-aa, archive.tgz.part-ab, ...

# 합치기
cat archive.tgz.part-* | tar xzf -
```

### 진행 표시 (`pv` 또는 `--checkpoint`)

```bash
sudo apt install pv
tar cf - dir/ | pv -s $(du -sb dir/ | awk '{print $1}') | gzip > archive.tgz

# 또는 checkpoint
tar -czf archive.tgz --checkpoint=1000 --checkpoint-action=dot dir/
```

## 15.8 증분 백업 (incremental)

```bash
# 풀 백업 + 스냅샷 파일
tar -czf full.tgz -g snapshot dir/

# 다음 번 호출 시: 변경분만
tar -czf inc1.tgz -g snapshot dir/
```

`-g` 의 snapshot 파일이 상태를 기억. 복원은 풀 → 증분 순서로:

```bash
tar -xzf full.tgz
tar -xzf inc1.tgz
```

(rsync/restic 류 백업이 더 편하지만 tar 만으로도 가능)

## 15.9 압축기 단독 사용

### gzip / gunzip

```bash
gzip file               # → file.gz, 원본 삭제
gzip -k file            # 원본 유지
gzip -9 file            # 최대 압축
gzip -d file.gz         # = gunzip
gunzip file.gz
zcat file.gz            # 풀지 않고 stdout
zless file.gz           # 풀지 않고 less
zgrep PAT file.gz       # 풀지 않고 grep (이 책 grep 제외이지만 zgrep은 별도)
```

### bzip2

```bash
bzip2 file
bunzip2 file.bz2
bzcat file.bz2
```

### xz

```bash
xz file
xz -d file.xz
xzcat file.xz
xz -9e file              # 강한 압축 (extreme)
xz -T 4 file             # 4스레드
```

### zstd (현대적, 빠르고 작음)

```bash
sudo apt install zstd
zstd file                # → file.zst
zstd -d file.zst
zstd -19 --long file     # 강한 압축
zstd -T0 file            # 사용 가능한 모든 코어
```

### 비교 (대략)

| 압축기 | 속도 | 비율 | 메모리 |
|--------|------|------|--------|
| gzip | 빠름 | 보통 | 적음 |
| bzip2 | 느림 | 좋음 | 보통 |
| xz | 매우 느림 | 매우 좋음 | 큼 |
| zstd | 매우 빠름 | 좋음 | 보통 |

요즘은 **zstd 가 거의 모든 면에서 합리적**. 패키지 (debian, arch)는 이미 .zst 사용 중.

## 15.10 zip / unzip — 윈도 호환

```bash
sudo apt install zip unzip

# 만들기
zip -r project.zip project/
zip -r project.zip project/ -x '*.tmp' '*/.git/*'
zip project.zip file1 file2

# 풀기
unzip project.zip
unzip project.zip -d /opt/
unzip -l project.zip       # 목록만
unzip -p project.zip file > file    # stdout

# 비밀번호 (약함, 신뢰 X)
zip -e secret.zip files/
unzip secret.zip            # 패스워드 묻기
```

| zip 옵션 | 의미 |
|----------|------|
| `-r` | 재귀 |
| `-x PAT` | 제외 |
| `-9` | 최대 압축 |
| `-0` | 무압축 (스토어만) |
| `-e` | 암호화 (전통 zip, 약함) |
| `-j` | 경로 정보 빼고 (junk paths) |
| `-u` | 업데이트 |

zip 의 암호화는 약하다. 강하게 하려면 7z `--mode=AES256` 또는 GPG.

## 15.11 7z — 강한 압축

```bash
sudo apt install p7zip-full

# 만들기
7z a archive.7z dir/

# AES-256 암호 + 헤더까지 암호화
7z a -p -mhe=on secret.7z files/

# 풀기
7z x archive.7z

# 목록
7z l archive.7z

# 다른 형식 다루기
7z x file.tar.xz
7z a -ttar archive.tar dir/
```

## 15.12 GPG 로 암호화 압축

zip/7z 의 패스워드는 약하므로 진짜 보안은 GPG.

```bash
tar czf - dir/ | gpg -c -o archive.tgz.gpg

# 풀기
gpg -d archive.tgz.gpg | tar xzf -

# 비대칭
tar czf - dir/ | gpg --encrypt -r alice@example.com > archive.tgz.gpg
```

## 15.13 검증 / 무결성

```bash
# tar 의 ok 여부
tar tzf archive.tgz > /dev/null && echo OK

# 해시 동봉
sha256sum archive.tgz > archive.tgz.sha256
sha256sum -c archive.tgz.sha256
```

배포할 때는 항상 해시도 같이.

## 15.14 cpio (구식)

`tar` 대안. 백업 시스템(예: initramfs)에서 여전히 보임.

```bash
find . | cpio -ov > archive.cpio
cpio -idv < archive.cpio
```

흔히 만나는 일은 RPM 풀 때:

```bash
rpm2cpio package.rpm | cpio -idmv
```

## 15.15 Termux 특이사항

- 외부 저장소에 큰 .tgz 만들 때 SAF 정책으로 느림 → `~/storage/shared/...` 보다 `$HOME` 안에서 먼저 만들고 옮겨라.
- xz 는 메모리 많이 먹음 → 대용량은 `xz -T 2 --memlimit-compress=512MiB`

## 15.16 자주 쓰는 한 줄 모음

```bash
# 빠른 풀백업
sudo tar --xattrs --acls -czpf /mnt/backup/etc-$(date +%F).tgz -C / etc

# 홈 디렉토리 백업 (제외 잔뜩)
tar --exclude-vcs-ignores --exclude='*.iso' --exclude='Cache' \
    -caf home-$(date +%F).tar.zst -C / home/$USER

# 원격으로 곧장 백업
tar czf - /var/www | ssh backup@host "cat > /backups/www-$(date +%F).tgz"

# .deb 안 풀어 보기
ar tv pkg.deb
ar x pkg.deb
tar tf data.tar.xz

# .rpm 풀기
rpm2cpio pkg.rpm | cpio -idmv

# zip 안의 한글 파일명 깨짐
unzip -O CP949 archive.zip      # 윈도산 zip
unzip -O UTF-8 archive.zip

# zstd 빠른 백업
tar -I 'zstd -T0 -19 --long' -cf archive.tar.zst dir/
tar -I 'zstd -d' -xf archive.tar.zst
```

다음 챕터: [제16장]

\newpage

---


# 16. 링크와 파일 정보 — ln, file, stat, which, md5sum

> 파일이 무엇인지 정확히 알기. 링크 구조를 의도대로 다루기.

## 16.1 하드링크 vs 심볼릭 링크

- **하드링크**: 같은 inode를 가리키는 다른 이름. 원본/사본 구분 없음.
- **심볼릭링크**: 다른 경로를 가리키는 작은 텍스트 파일.

| 특성 | 하드링크 | 심볼릭링크 |
|------|----------|------------|
| 원본 삭제 시 | 데이터 보존 | 깨진 링크 |
| 디렉토리에 가능? | 보통 X (root 만 -d) | O |
| 다른 파일시스템 가능? | X | O |
| inode | 같음 | 다름 |
| `ls -l` 표시 | 보통 파일 | `l` + `→` |
| 권한 | 원본과 공유 | 자신의 (보통 777, 의미 X) |

## 16.2 ln — 링크 만들기

```bash
ln -s TARGET LINK         # 심볼릭
ln    TARGET LINK         # 하드링크

# 디렉토리 심볼릭링크
ln -s /data/big /home/user/data

# 강제 덮어쓰기
ln -sf /new/target link

# 상대 경로 심볼릭
ln -sr /opt/app/bin /usr/local/bin/app
# (ln -s 는 인자를 그대로 저장 → 상대 경로 만들고 싶을 때 -r)

# 다중 (디렉토리에 같은 이름으로)
ln -s /opt/{a,b,c}.cfg /etc/

# 백업하면서 변경
ln -sb -f /new/target link        # 기존을 link~ 로
```

| 옵션 | 의미 |
|------|------|
| `-s` | 심볼릭 (기본은 하드) |
| `-f` | 강제 (기존 덮어씀) |
| `-i` | 확인 |
| `-n` | 디렉토리 심볼릭을 디렉토리 취급 X |
| `-r` | 상대 경로 (TARGET 을 LINK 기준 상대로) |
| `-v` | verbose |
| `-T` | LINK가 항상 새 링크명 (디렉토리 끝에 만들기 회피) |
| `-b` | 덮을 때 백업 |
| `-S SUF` | 백업 접미사 |

### 상대 vs 절대 — 흔한 실수

```bash
# 잘못된 상대 (현재 디렉토리 기준으로 저장됨)
cd /home/user
ln -s ../data link        # → ../data 그대로 저장 → /home/user/.. 가 되버림

# 안전: -r 로 LINK 위치 기준 상대 자동
ln -sr /data/x /home/user/x

# 또는 절대경로로
ln -s /data/x /home/user/x
```

### 깨진 링크 점검

```bash
# 링크지만 대상이 없는 것
find . -xtype l

# 또는 readlink 로 확인
readlink -e link        # 존재해야만 출력
readlink -f link        # 정규화 (없어도 출력 시도)
readlink link           # 그냥 가리키는 값
```

### 디렉토리 심볼릭 함정

```bash
ln -s /data/log /var/log
cd /var/log
cd ..        # 어디로 가는가? → /var (논리적, 셸 PWD 기준)
ls /var/log/../   # → /data/ (실제 inode 기반)
```

`-L` (논리적, 기본) 과 `-P` (물리적) 을 알아두자. `pwd -P`, `cd -P`.

## 16.3 file — 내용 보고 형식 추측

```bash
file image.png
# → image.png: PNG image data, 1920 x 1080, 8-bit/color RGBA

file script
# → script: Bourne-Again shell script, ASCII text executable

file binary
# → binary: ELF 64-bit LSB executable, x86-64, ...
```

| 옵션 | 의미 |
|------|------|
| `-b` | 파일명 빼고 |
| `-i` | MIME 타입 |
| `-z` | 압축파일 안까지 |
| `-L` | 심볼릭 따라감 |
| `-h` | 심볼릭 그대로 |
| `-s` | 디바이스 파일도 |
| `-f LIST` | 파일 목록 |

```bash
file -i config.txt              # → text/plain; charset=utf-8
file -b photo.jpg               # → JPEG image data, ...
file --mime-type photo.jpg      # → image/jpeg
```

## 16.4 stat — 메타데이터 정밀 조회

```bash
stat file
```

출력:

```
  File: file
  Size: 1234         Blocks: 8          IO Block: 4096   regular file
Device: 802h/2050d   Inode: 12345        Links: 1
Access: (0644/-rw-r--r--)  Uid: ( 1000/seunghwa)   Gid: ( 1000/seunghwa)
Access: 2026-05-07 09:00:00.000000000 +0900
Modify: 2026-05-06 18:30:00.000000000 +0900
Change: 2026-05-06 18:30:00.000000000 +0900
 Birth: 2025-12-01 12:00:00.000000000 +0900
```

| 시간 | 의미 |
|------|------|
| Access (atime) | 마지막 읽기 |
| Modify (mtime) | 마지막 내용 수정 |
| Change (ctime) | inode 변경 (권한, 이름, 링크 수 등) |
| Birth | 생성 (지원 파일시스템만) |

### 포맷 출력

```bash
stat -c '%s' file              # 크기
stat -c '%y' file              # mtime (사람용)
stat -c '%Y' file              # mtime (epoch)
stat -c '%a %n' file           # 권한 8진 + 이름
stat -c '%U:%G %a %n' file
stat -c '%F' file              # 파일 종류
stat -c '%i' file              # inode
stat -c '%h' file              # 하드링크 수
```

| 토큰 | 의미 |
|------|------|
| `%n` | 이름 |
| `%s` | 크기 |
| `%a`/`%A` | 권한(8진/문자) |
| `%U`/`%G` | 사용자/그룹 |
| `%y`/`%Y` | mtime |
| `%w`/`%W` | birth |
| `%i` | inode |
| `%h` | 링크 수 |
| `%F` | 파일 종류 |
| `%T` | 디바이스 마이너 |
| `%t` | 디바이스 메이저 |
| `%b` | 블록 |
| `%B` | 블록 크기 |
| `%o` | I/O 블록 |

`stat -f /` 는 **파일시스템** 정보:

```bash
stat -f -c '%T %a/%b' /        # 타입, free/total 블록
```

## 16.5 which / whereis / type / command -v / hash

| 도구 | 무엇 |
|------|------|
| `which CMD` | PATH 에서 실행파일 위치 |
| `whereis CMD` | 바이너리 + 매뉴얼 + 소스 |
| `type CMD` | 셸 빌트인/별칭/함수까지 (셸 빌트인) |
| `command -v CMD` | type 의 POSIX 표준 (스크립트용) |
| `hash` | 셸이 캐싱한 명령 위치 |

```bash
which python
# /usr/bin/python

type python
# python is /usr/bin/python

type ll
# ll is aliased to `ls -l`

command -v node && echo found
```

스크립트에서 명령 존재 검사는 `command -v`.

```bash
if command -v jq >/dev/null; then
  jq . file.json
else
  echo "jq 가 필요합니다"; exit 1
fi
```

`type`은 `command` 보다 풍부하지만 셸별로 약간 다르다. 이식성은 `command -v`.

## 16.6 readlink, realpath

```bash
readlink link             # 가리키는 값
readlink -f link          # 정규화 (없는 경로도)
readlink -e link          # 정규화 + 존재 확인
realpath path             # 절대경로 정규화
realpath --relative-to=/home /home/user/x   # → user/x
```

스크립트 자기 위치 알아내기:

```bash
SELF="$(realpath "$0")"
DIR="$(dirname "$SELF")"
```

## 16.7 파일 해시 — md5sum, sha1sum, sha256sum, sha512sum

```bash
md5sum file
sha256sum file > file.sha256
sha256sum -c file.sha256

# 디렉토리 통째로
find . -type f -print0 | xargs -0 sha256sum > all.sha256
```

검증:

```bash
sha256sum -c all.sha256
# file: OK
# other: FAILED
# sha256sum: WARNING: 1 computed checksum did NOT match
```

### 자주 쓰는 패턴

```bash
# 큰 파일 빠르게 비교
sha256sum local.iso
ssh host "sha256sum /remote/iso"

# 변조 감지
find /etc -type f -print0 | xargs -0 sha256sum > /var/etc-baseline.sha256
# 나중에:
find /etc -type f -print0 | xargs -0 sha256sum -c /var/etc-baseline.sha256 \
  | grep -v ': OK$'
```

### 어떤 해시?

| 알고리즘 | 용도 |
|----------|------|
| md5 | 무결성 (충돌 가능, 보안 X) |
| sha1 | 무결성 (사실상 폐기) |
| sha256 | **권장** |
| sha512 | 매우 큰 파일에 |
| blake3 / b2sum | 빠르고 안전, 새 시스템 |

## 16.8 cmp — 바이너리 비교

```bash
cmp a.bin b.bin                 # 다르면 첫 바이트 위치 알림
cmp -s a.bin b.bin && echo same
cmp -n 1024 a.bin b.bin         # 처음 1KB 만
```

## 16.9 du — 사용량 (간단히)

```bash
du -sh dir/                # 디렉토리 합계, human readable
du -h --max-depth=1 dir/   # 1단계 까지
du -ah . | sort -h | tail  # 큰 것부터
du -sh * 2>/dev/null | sort -h
du --apparent-size -sh dir/   # 논리적 크기 (sparse 진실)
```

자세한 디스크 분석은 [제41장].

## 16.10 lsattr / chattr — 파일시스템 속성 (ext4)

```bash
lsattr file
chattr +i file       # immutable (root 도 수정 불가)
chattr -i file
chattr +a logfile    # append only
```

`+i` 는 백업 단단히 보호, `+a` 는 로그 변조 방지.

주의: `chmod`/`rm` 이 안 통하니, 작업 끝나면 반드시 `-i` 해제 후 정리.

## 16.11 dirname / basename

```bash
dirname /a/b/c.txt        # /a/b
basename /a/b/c.txt       # c.txt
basename /a/b/c.txt .txt  # c
```

스크립트:

```bash
SELF="$(realpath "$0")"
DIR="$(dirname "$SELF")"
NAME="$(basename "$SELF" .sh)"
```

## 16.12 touch — 시간 / 빈 파일

```bash
touch file                            # 없으면 만들고, 있으면 mtime 갱신
touch -c file                         # 없으면 만들지 않음
touch -t 202605070900 file            # YYYYMMDDhhmm
touch -d '2026-05-01 09:00' file
touch -r ref file                     # ref 의 시간으로 맞춤
touch -m file                         # mtime 만
touch -a file                         # atime 만
```

빈 파일 일괄 생성:

```bash
touch a{1..10}.log
```

## 16.13 inode / 파일 시스템 한계

```bash
df -i        # inode 사용량
ls -i file   # inode 번호
```

작은 파일이 무수히 많으면 디스크는 남았는데 inode 가 고갈될 수 있다(`No space left on device`인데 `df -h`엔 여유). `df -i` 로 확인.

## 16.14 자주 쓰는 한 줄

```bash
# 깨진 심볼릭링크 다 찾기
find / -xtype l 2>/dev/null

# 큰 파일 5개 (sparse 무시)
find / -xdev -type f -printf '%s %p\n' 2>/dev/null | sort -rn | head -5

# 디렉토리 트리에서 inode 사용량
find . -xdev | wc -l

# 파일 내용 동일 확인 (큰 파일도 빠르게)
[ "$(sha256sum a | awk '{print $1}')" = "$(sha256sum b | awk '{print $1}')" ] && echo same

# bin 디렉토리 모두에 같은 스크립트 심볼릭
for d in /usr/local/bin /opt/bin; do
  ln -sf /opt/app/run.sh $d/app
done

# 모든 ssh 키 지문
for k in ~/.ssh/*.pub; do
  ssh-keygen -lf "$k"
done
```

다음 챕터: [제17장]

\newpage

---


# 17. sed — 스트림 에디터

> 텍스트를 흐름처럼 변환. 파일 일괄 치환의 표준.

## 17.1 sed 모델

- 입력을 한 줄씩 읽어 **패턴 스페이스**에 둠
- 스크립트(주소 + 명령)를 적용
- 결과를 출력 (또는 `-i` 로 파일 직접 수정)

```
sed [옵션] '주소 명령;주소 명령;...' [파일]
```

## 17.2 옵션

| 옵션 | 의미 |
|------|------|
| `-n` | 자동 출력 끔 (필요 시 `p` 명령) |
| `-e CMD` | 명령 추가 |
| `-f FILE` | 명령 파일 |
| `-i[SUFFIX]` | in-place 수정 (`-i` 또는 `-i.bak`) |
| `-E` 또는 `-r` | 확장 정규식 |
| `-s` | 다중 파일을 별개로 처리 |
| `-z` | 라인 구분을 NUL 로 |
| `--posix` | POSIX 모드 |

GNU sed 와 BSD/macOS sed 차이:
- macOS: `sed -i '' 's/a/b/' file` (빈 인자 필수)
- GNU: `sed -i 's/a/b/' file`
- 호환: `sed -i.bak ...` 양쪽 다 OK

## 17.3 핵심 명령

| 명령 | 의미 |
|------|------|
| `p` | 출력 |
| `d` | 삭제 (다음 줄로) |
| `s/PAT/REP/FLAGS` | 치환 |
| `y/SRC/DST/` | 문자별 변환 (tr 비슷) |
| `a TEXT` | 다음 줄에 추가 |
| `i TEXT` | 이전 줄에 삽입 |
| `c TEXT` | 줄 교체 |
| `q` | 종료 |
| `Q` | 출력 없이 종료 |
| `n` | 다음 줄 읽음 |
| `N` | 다음 줄을 패턴 스페이스에 이어붙임 |
| `b LABEL` | 점프 |
| `t LABEL` | 직전 s 성공 시 점프 |
| `=` | 라인 번호 출력 |
| `l` | 비인쇄 문자 표시 |
| `r FILE` | 파일 읽어 출력 |
| `w FILE` | 패턴 스페이스를 파일에 |
| `x` | 패턴/홀드 스페이스 교환 |
| `g` | 홀드 → 패턴 |
| `h` | 패턴 → 홀드 |
| `G` | 홀드 추가 |
| `H` | 홀드에 추가 |

## 17.4 주소 (어디에 적용할까)

```bash
sed '5d'             # 5번 줄 삭제
sed '5,10d'          # 5~10
sed '5,$d'           # 5부터 끝까지
sed '$d'             # 마지막 줄
sed '/PAT/d'         # 패턴 매칭 줄 삭제
sed '/^#/d'          # 주석 줄 삭제
sed '/^$/d'          # 빈 줄 삭제
sed '/start/,/end/d' # 두 패턴 사이
sed '0~2d'           # 짝수 줄 삭제 (GNU: every 2nd)
sed '1~3p'           # 1, 4, 7, ...
sed '/PAT/!d'        # PAT 매칭 안 되는 줄 삭제 (= 매칭만 남김)
```

`addr1,addr2` 의 두 패턴 모드: 시작 만나면 켜고, 끝 만나면 끔.

## 17.5 치환 — s 명령

```bash
sed 's/old/new/' file              # 줄당 첫 매치만
sed 's/old/new/g' file             # 줄당 모두
sed 's/old/new/2' file             # 2번째 매치만
sed 's/old/new/gi' file            # 대소문자 무시 (GNU)
sed 's|old|new|g' file             # / 가 본문에 많을 때 다른 구분자
sed 's:old:new:g' file
```

### 치환 플래그

| 플래그 | 의미 |
|--------|------|
| `g` | 모든 매치 |
| `N` | N번째 매치 |
| `gN` | N번째부터 끝까지 |
| `i`, `I` | 대소문자 무시 |
| `p` | 매칭 시 출력 |
| `w FILE` | 결과를 파일에 |
| `e` | 결과를 셸 명령으로 (위험) |

### 캡처 그룹

```bash
sed -E 's/^([0-9]+)-(.+)$/\2 (#\1)/' file
# 123-hello → hello (#123)

# & 는 매치 전체
sed 's/[0-9]+/<&>/g' file
# 1 2 3 → <1> <2> <3>
```

GNU 확장: `\U` 대문자, `\L` 소문자, `\u` 첫글자 대문자, `\l` 첫글자 소문자, `\E` 종료.

```bash
echo "hello world" | sed 's/.*/\U&/'      # → HELLO WORLD
echo "hello world" | sed 's/\b./\u&/g'    # → Hello World
```

## 17.6 in-place 수정

```bash
# 백업 만들고 수정
sed -i.bak 's/foo/bar/g' file

# 백업 없이 (조심)
sed -i 's/foo/bar/g' file

# 다중 파일
sed -i 's/foo/bar/g' *.conf
sed -i 's/foo/bar/g' file1 file2 file3

# 디렉토리 트리 일괄
find . -type f -name '*.md' -print0 | xargs -0 sed -i 's/foo/bar/g'

# git 추적 파일만
git ls-files -z | xargs -0 sed -i 's/foo/bar/g'
```

`-i.bak`: `file` 는 새 내용, `file.bak` 은 원본. 검증 후:

```bash
diff file file.bak
rm file.bak    # 또는 한꺼번에 find 로 정리
```

## 17.7 자주 쓰는 패턴

### 빈 줄 / 주석 정리

```bash
sed '/^\s*$/d; /^\s*#/d' config.ini
```

### 앞뒤 공백 제거

```bash
sed -E 's/^[[:space:]]+|[[:space:]]+$//g' file
```

### N 줄만 출력 (head 대체)

```bash
sed -n '1,10p' file        # 1~10
sed '10q' file             # 10 보고 종료 (head 대비 매우 빠름)
```

### 마지막 N 줄

(sed 단독은 약함, 보통 `tail` 사용)

### 특정 패턴부터 끝까지 / 사이

```bash
sed -n '/START/,/END/p' file
sed '/START/,/END/d' file
```

### 줄 번호 매기기

```bash
sed = file | sed 'N;s/\n/\t/'
```

### 한 줄을 N번 복제

```bash
sed 'p' file               # 모든 줄 두 번
```

### Windows 줄끝 → Unix

```bash
sed -i 's/\r$//' file
# 또는
dos2unix file
```

### Unix → Windows

```bash
sed -i 's/$/\r/' file
# 또는
unix2dos file
```

### 라인 번호로 추가 / 삽입

```bash
sed '5a inserted line' file       # 5번 다음에
sed '5i inserted line' file       # 5번 이전에
sed '$a appended' file            # 마지막에 추가
```

### 파일에 헤더 박기

```bash
sed -i '1i # 자동 생성됨' file
```

### 첫 매치만 변경

```bash
sed '0,/foo/{s/foo/bar/}' file
```

### 줄 합치기 (다음 줄 이어붙임)

```bash
sed ':a;N;$!ba;s/\n/ /g' file
# 모든 \n 을 공백으로 (= 한 줄로)
```

### 두 줄짜리 주소 — 다중 매칭

```bash
sed '/^server {/,/^}/{ s/listen 80/listen 8080/ }' nginx.conf
```

## 17.8 여러 명령

```bash
# -e 여러 번
sed -e 's/foo/bar/' -e 's/baz/qux/' file

# 세미콜론으로 구분
sed 's/foo/bar/; s/baz/qux/' file

# 묶음
sed '/^#/{ s/foo/bar/; s/baz/qux/ }' file

# 스크립트 파일
cat > tidy.sed <<'EOF'
/^\s*$/d
/^\s*#/d
s/[[:space:]]+$//
EOF
sed -f tidy.sed input.txt
```

## 17.9 홀드 스페이스 트릭

홀드 스페이스는 sed의 보조 버퍼.

```bash
# 라인 거꾸로
sed '1!G;h;$!d' file      # tac 동작

# 빈 줄 두 줄을 한 줄로
sed '/^$/N;/\n$/d' file
```

홀드 스페이스 활용은 강력하지만 가독성이 떨어진다. 복잡해지면 awk/python 으로 가는 게 낫다.

## 17.10 디버깅

```bash
# 매 단계 출력 (GNU)
sed --debug 's/foo/bar/g' file

# 매 줄 번호 + 내용
sed = file | sed 'N;s/\n/ /'

# 적용 미리보기 (in-place 전에)
sed 's/foo/bar/g' file | diff file -
```

## 17.11 흔한 함정

| 함정 | 대처 |
|------|------|
| `/` 가 본문에 있어 깨짐 | 다른 구분자 `s|x|y|` |
| 백슬래시 폭발 | 따옴표를 작은(') 으로 |
| GNU/BSD 차이 (`-i` 인자 등) | `-i.bak` 호환 트릭 |
| 정규식 욕심 매칭 | `[^/]` 같은 negated 클래스 |
| Windows 라인 안 잡힘 | `\r$` 제거 먼저 |
| in-place 가 심볼릭링크 끊음 | `--follow-symlinks` (GNU) |
| 한글 안에서 `[a-z]` | 정상 동작 (UTF-8 단위) |

## 17.12 자주 쓰는 한 줄 모음

```bash
# 라인 N만 출력
sed -n '42p' file

# 라인 N부터 끝까지
sed -n '10,$p' file

# 처음과 끝 빼고
sed '1d;$d' file

# 마지막 줄
sed -n '$p' file

# 라인 수 (wc -l 같음)
sed -n '$=' file

# 짝수 줄 / 홀수 줄
sed -n '1~2p' file
sed -n '2~2p' file

# 첫 비주석 줄
sed -n '/^[^#]/{p;q}' file

# 빈 줄 제거
sed '/^$/d' file

# 키=값 에서 값만
sed -n 's/^FOO=//p' file

# 파일 머리에 라이선스 주입
sed -i '1i# Copyright 2026' *.py

# yum / apt 출력 깔끔하게
... | sed -e '/^Reading/d' -e '/^Loading/d'

# 들여쓰기 변환 (탭→4 스페이스)
sed -i 's/\t/    /g' file
```

## 17.13 awk 와 grep 이 더 어울릴 때

이 책에서 awk/grep 은 제외 대상이지만, 다음은 sed로 무리하지 말자:

- 컬럼 단위 처리 → awk
- 패턴 검색 → grep / ripgrep
- JSON / CSV / YAML → jq, csvkit, yq
- 다중 줄 복잡 변환 → python

sed 는 **단순 치환과 라인 필터의 챔피언**. 그 이상은 바로 옮겨라.

다음 챕터: [제18장]

\newpage

---


# 18. cut / sort / uniq / tr / paste / join

> 컬럼 자르고, 정렬하고, 중복 추리고, 글자 바꾸고. 텍스트 파이프의 기본 부품.

## 18.1 cut — 컬럼 자르기

```bash
cut -d',' -f1,3 file.csv          # 1, 3번째 필드 (콤마 구분)
cut -d':' -f1 /etc/passwd          # 사용자명
cut -d' ' -f2- file                # 2번째부터 끝까지
cut -c1-10 file                    # 첫 10글자 (바이트)
cut -c5- file                      # 5글자부터 끝
cut -b1-3 file                     # 바이트 단위
cut --complement -d',' -f2 file    # 2번 필드 빼고 모두
```

| 옵션 | 의미 |
|------|------|
| `-d D` | 구분자 |
| `-f LIST` | 필드 (1, 3-5, 2-) |
| `-c LIST` | 문자 |
| `-b LIST` | 바이트 |
| `--complement` | 반대 (지정 외 출력) |
| `-s` | 구분자 없는 줄 무시 |
| `--output-delimiter=D` | 출력 구분자 |

cut 의 한계: 다중 공백 같은 가변 구분자 처리 약함. 그땐 awk.

```bash
# ls -l 같이 다중 공백
ps aux | tr -s ' ' | cut -d' ' -f2,11
# 또는
ps aux | awk '{print $2,$11}'   # awk 가 자연스러움
```

## 18.2 sort — 정렬

```bash
sort file                    # 사전순
sort -n file                 # 숫자
sort -h file                 # 사람 읽기 (1K, 2M, 3G)
sort -r file                 # 역순
sort -u file                 # 중복 제거
sort -k2 file                # 2번째 필드 기준
sort -k2,2 -t',' file        # 콤마 구분, 2번 필드만
sort -k3n file               # 3번 필드 숫자 정렬
sort -t':' -k3 -n /etc/passwd  # passwd 의 UID
sort -V file                 # 버전 정렬 (1.10 > 1.9)
sort -M file                 # 월 이름
sort -R file                 # 무작위
sort --parallel=4 huge.txt
```

| 옵션 | 의미 |
|------|------|
| `-n` | 숫자 |
| `-h` | human size |
| `-r` | 역 |
| `-u` | unique |
| `-f` | 대소문자 무시 |
| `-d` | 사전 (영숫자, 공백만) |
| `-i` | 비인쇄 무시 |
| `-V` | 버전 |
| `-M` | 월 |
| `-R` | 랜덤 |
| `-k F[,L]` | 키 필드 |
| `-t SEP` | 구분자 |
| `-s` | 안정 정렬 |
| `-b` | 앞 공백 무시 |
| `-c` | 정렬되어 있는지 검사만 |
| `-m` | 이미 정렬된 파일들 병합 |
| `-T DIR` | 임시 디렉토리 |
| `-S SIZE` | 메모리 |
| `-z` | NUL 구분 |
| `--parallel=N` | 병렬 |

### 다중 키

```bash
# 2번 필드 숫자 ↑, 동률은 1번 필드 ↑
sort -t',' -k2,2n -k1,1 file

# 사이즈 ↓ 후 이름
ls -l | sort -k5,5nr -k9,9
```

### 큰 파일

`sort` 는 외부 정렬을 자동으로 한다(메모리 안 넘침). 임시 공간 잘 봐야 함:

```bash
sort -T /var/tmp -S 1G huge.txt > sorted.txt
```

## 18.3 uniq — 중복 처리

`uniq` 은 **인접한** 중복만 처리. 그래서 보통 `sort | uniq`.

```bash
sort file | uniq                      # 중복 제거
sort file | uniq -c                   # 개수
sort file | uniq -c | sort -rn        # 빈도 순
sort file | uniq -d                   # 중복된 것만
sort file | uniq -u                   # 단 한 번 등장한 것만
sort -u file                          # uniq 없이도 가능
```

| 옵션 | 의미 |
|------|------|
| `-c` | 개수 prefix |
| `-d` | 중복만 |
| `-u` | 유일만 |
| `-i` | 대소문자 무시 |
| `-f N` | 첫 N 필드 무시 |
| `-s N` | 첫 N 문자 무시 |
| `-w N` | 첫 N 문자만 비교 |

### 빈도 분석 (가장 많은 사용 패턴)

```bash
# 가장 많이 등장한 IP (access log)
awk '{print $1}' access.log | sort | uniq -c | sort -rn | head
# (awk 빠지면)
cut -d' ' -f1 access.log | sort | uniq -c | sort -rn | head

# 가장 많은 확장자
ls | sed 's/.*\.//' | sort | uniq -c | sort -rn
```

## 18.4 tr — 단일 문자 변환

`sed` 와 다르게 정규식이 없다. 문자→문자 매핑.

```bash
echo "Hello" | tr 'a-z' 'A-Z'        # → HELLO
echo "Hello" | tr 'A-Z' 'a-z'
tr -d '\r' < dosfile > unixfile      # 캐리지리턴 제거
tr -d '[:space:]'                    # 공백류 모두 삭제
tr -s ' ' < file                     # 연속 공백 → 단일
tr -s '\n'                            # 연속 빈 줄 → 한 줄
tr -c 'A-Za-z0-9\n' '_'              # 알파숫자/줄바꿈 외 → _
```

| 옵션 | 의미 |
|------|------|
| `-d` | SET1 의 문자 삭제 |
| `-s` | SET1 의 연속을 한 번으로 |
| `-c` | SET1 의 보집합 |
| `-t` | SET1 길이로 자름 (truncate) |

### POSIX 클래스

| 클래스 | 의미 |
|--------|------|
| `[:alpha:]` | 알파벳 |
| `[:alnum:]` | 알파숫자 |
| `[:digit:]` | 숫자 |
| `[:upper:]` `[:lower:]` | 대/소문자 |
| `[:space:]` | 공백류 |
| `[:punct:]` | 구두점 |
| `[:cntrl:]` | 제어 문자 |
| `[:print:]` | 인쇄 가능 |
| `[:graph:]` | 인쇄 + 공백 X |
| `[:xdigit:]` | 16진 |

```bash
echo "Hello, World 123!" | tr -d '[:punct:]'
# Hello World 123
```

## 18.5 paste — 컬럼으로 붙이기

```bash
paste a.txt b.txt                 # 줄별로 옆에 붙임 (TAB)
paste -d',' a.txt b.txt           # 콤마 구분
paste -d',\n' a b c d             # 구분자 순환 (a,b\nc,d)
paste -s file                     # 모든 줄을 한 줄로 (TAB)
paste -sd',' file                 # 모든 줄을 한 줄로 (콤마)
seq 1 10 | paste -sd',' -         # 1,2,3,...,10
```

## 18.6 join — 두 파일을 키로 결합

```bash
# 파일 양쪽이 1번 필드로 정렬되어 있어야 함
join a.txt b.txt

# 다른 키 / 다른 구분자
join -t',' -1 1 -2 2 a.csv b.csv

# 매칭 안 되는 행도
join -a1 a.txt b.txt              # a 의 unmatched 도 출력
join -a1 -a2 a.txt b.txt          # 양쪽 모두

# 채울 값
join -e MISSING -o '0,1.2,2.2' -t',' a b
```

| 옵션 | 의미 |
|------|------|
| `-1 N` | 파일1 키 필드 |
| `-2 N` | 파일2 키 필드 |
| `-t SEP` | 구분자 |
| `-a N` | unmatched 도 (1, 2, 모두) |
| `-v N` | unmatched 만 |
| `-e VAL` | 빠진 값 채움 |
| `-o LIST` | 출력 형식 (`1.1,1.2,2.3`) |
| `-i` | 대소문자 무시 |

## 18.7 자주 쓰는 한 줄

```bash
# CSV에서 1, 3번 컬럼만
cut -d',' -f1,3 data.csv

# 이상한 구분자 → 정규화
sed -E 's/[[:space:]]+/,/g' raw.txt > clean.csv

# /etc/passwd에서 사용자/UID/홈
cut -d':' -f1,3,6 /etc/passwd | sort -t':' -k2,2n

# 가장 많이 등장한 단어 10개
tr -cs '[:alpha:]' '\n' < text.txt \
  | tr 'A-Z' 'a-z' \
  | sort \
  | uniq -c \
  | sort -rn \
  | head

# 파일에서 알파숫자만
tr -cd '[:alnum:]\n' < input.txt > clean.txt

# 임의 비밀번호 32자
LC_ALL=C tr -dc 'A-Za-z0-9!@#$%^&*' </dev/urandom | head -c 32; echo

# UUID 비슷한 거
LC_ALL=C tr -dc 'a-f0-9' </dev/urandom | head -c 32 | \
  sed 's/\(........\)\(....\)\(....\)\(....\)\(.*\)/\1-\2-\3-\4-\5/'

# 두 파일의 공통 라인
sort a > a.s; sort b > b.s; comm -12 a.s b.s

# 파일 간 차이 라인 만
comm -23 a.s b.s            # a 만 있는 라인
comm -13 a.s b.s            # b 만 있는 라인

# 행렬 전치 (간단한 경우)
paste -d',' <(cut -d',' -f1 file) <(cut -d',' -f2 file)
```

## 18.8 comm — 정렬된 두 파일 비교

```bash
comm a.s b.s
# 3 컬럼: a 만 / b 만 / 공통

comm -12 a.s b.s    # 공통만
comm -23 a.s b.s    # a 에만 있는
comm -13 a.s b.s    # b 에만 있는
comm -3 a.s b.s     # 차이만 (양쪽 unique)
```

`-N`은 N번째 컬럼을 **숨김**(빼는 것이 아니다). 양 파일 모두 정렬 필수.

## 18.9 split — 큰 파일 자르기

```bash
split -l 1000 big.csv chunk_         # 1000줄씩
split -b 100M big.iso chunk_         # 100MB 씩
split -n l/4 big.txt chunk_          # 4등분 (라인 경계)
split -d -a 4 big.csv chunk_         # 숫자 접미사 4자리
split -l 1000 big.csv chunk_ --additional-suffix=.csv
```

합치기:

```bash
cat chunk_* > restored.csv
```

CSV 헤더 보존:

```bash
head -1 big.csv > header
tail -n +2 big.csv | split -l 1000 - chunk_ --filter='cat header - > $FILE'
```

## 18.10 종합 패턴 — log 분석

access.log:
```
1.2.3.4 - - [07/May/2026:09:00:00] "GET /api/users HTTP/1.1" 200 1234
```

- 가장 많이 본 IP:

```bash
cut -d' ' -f1 access.log | sort | uniq -c | sort -rn | head
```

- 시간대별 요청 수:

```bash
cut -d'[' -f2 access.log | cut -d']' -f1 | cut -d':' -f1-2 \
  | sort | uniq -c
```

- 5xx 에러만:

```bash
sed -n 's/.* "[A-Z]* \([^ ]*\) HTTP[^"]*" \(5[0-9][0-9]\) .*/\2 \1/p' access.log \
  | sort | uniq -c | sort -rn
```

다음 챕터: [제19장]

\newpage

---


# 19. wc / head / tail / less / more

> 카운팅과 페이저. 큰 파일을 보는 기본 도구.

## 19.1 wc — 단어/줄/바이트 카운트

```bash
wc file
# 12  34  567 file
# 줄  단어 바이트

wc -l file        # 줄 수
wc -w file        # 단어 수
wc -c file        # 바이트
wc -m file        # 문자 (멀티바이트 인식)
wc -L file        # 가장 긴 줄 길이
```

다중 파일:

```bash
wc -l *.md
# ...
# total 1234
```

stdin:

```bash
ps aux | wc -l        # 프로세스 수 (헤더 +1)
```

### 자주 쓰는 패턴

```bash
# 파일 줄수 한 줄로
wc -l < file              # 파일명 빠짐 (값만)

# 디렉토리 트리 라인 합계
find . -type f -name '*.go' -print0 | xargs -0 wc -l | tail -1

# 한글이 포함된 줄 길이
wc -m file                # 문자 단위
wc -c file                # 바이트 단위 (한글 3바이트면 차이남)
```

## 19.2 head — 앞부분

```bash
head file               # 기본 10줄
head -n 20 file
head -n -5 file         # 마지막 5줄 빼고 모두
head -c 100 file        # 첫 100바이트
head -q *.log           # 다중 파일에서 헤더 (==> file <==) 안 보임
head -v file            # 헤더 강제 표시
```

`-n -K` (음수)는 GNU 확장이지만 매우 유용.

## 19.3 tail — 뒷부분

```bash
tail file               # 기본 10줄
tail -n 20 file
tail -n +5 file         # 5번째 줄부터 끝까지 (1 기반)
tail -c 100 file        # 마지막 100바이트
tail -f file            # follow (새로 추가되는 줄 출력)
tail -F file            # follow + 로테이션 추적
tail -f file1 file2     # 다중 파일 동시 추적
tail --pid=PID -f file  # 프로세스 죽으면 종료
tail -s 5 -f file       # 폴링 간격 5초 (기본 1초)
```

### -f 와 -F 의 차이

- `-f`: inode 추적. `logrotate`로 새 파일이 만들어지면 옛 inode 만 보고 있음.
- `-F` = `--follow=name --retry`: 같은 **이름** 추적. 로테이션 후에도 새 파일을 본다.

운영 로그는 거의 항상 `tail -F`.

```bash
sudo tail -F /var/log/nginx/access.log
sudo tail -F /var/log/syslog /var/log/auth.log
```

### tail -f + grep 으로 실시간 필터

```bash
tail -F /var/log/nginx/access.log | grep -i error
# 또는 grep 제외 책이라면
tail -F /var/log/nginx/access.log | sed -n '/error/Ip'
```

### 따라가다가 파일 회전 감지

```bash
sudo tail -F --max-unchanged-stats=5 /var/log/syslog
```

## 19.4 less — 표준 페이저

```bash
less file
less +F file        # tail -f 모드로 시작
less +G file        # 끝에서 시작
less +/PAT file     # 검색하면서 시작
less -N file        # 라인 번호
less -S file        # 긴 줄 자름 (가로 스크롤)
less -R file        # ANSI 컬러 그대로
less -i file        # 검색 대소문자 무시 (소문자만)
less -I file        # 검색 항상 무시
less -X file        # 종료 시 화면 클리어 안 함
```

### 핵심 단축키

| 키 | 동작 |
|----|------|
| `Space` / `f` / `Ctrl+F` | 다음 페이지 |
| `b` / `Ctrl+B` | 이전 페이지 |
| `d` / `u` | 반 페이지 |
| `↓` `↑` | 한 줄 |
| `g` | 첫 페이지 |
| `G` | 마지막 페이지 |
| `Ng` | N 번째 줄 |
| `/PAT` | 정방향 검색 |
| `?PAT` | 역방향 검색 |
| `n` `N` | 다음/이전 매치 |
| `&PAT` | 매치 줄만 표시 (필터) |
| `&` Enter | 필터 해제 |
| `m c` | 마크 c 저장 |
| `'c` | 마크 c 로 점프 |
| `''` | 직전 위치 |
| `=` 또는 `Ctrl+G` | 현재 위치 정보 |
| `:n` `:p` | 다중 파일 다음/이전 |
| `v` | $EDITOR 로 편집 |
| `F` | tail -f 모드 |
| `Ctrl+C` | F 모드 빠져나오기 |
| `R` | 화면 강제 갱신 |
| `q` 또는 `Q` | 종료 |
| `h` | 도움말 |

### 매우 유용한 환경변수

```bash
export LESS="-R -i -F -X"      # ~/.bashrc
# -R: 컬러
# -i: 대소문자 무시
# -F: 한 화면이면 자동 종료
# -X: 화면 안 지움 (스크롤백 보존)
```

man, git, journalctl 등 거의 모든 페이저 호출이 영향받음.

### 압축 파일 보기 — zless / xzless / zstdless

```bash
zless file.gz
xzless file.xz
bzless file.bz2
zstdless file.zst
```

또는 `lesspipe` 가 활성화되어 있으면 `less file.gz` 그대로:

```bash
eval "$(lesspipe)"          # ~/.bashrc 흔히
```

## 19.5 more — less 의 구식 형

```bash
more file
```

기능 적음. less 가 거의 모든 환경에 깔려 있어 굳이 쓸 일 없다. 단, BusyBox 의 임베디드/구식 시스템에는 more 만 있을 수 있음.

`more` 단축키 일부:

| 키 | 동작 |
|----|------|
| `Space` | 다음 페이지 |
| `Enter` | 한 줄 |
| `q` | 종료 |
| `/PAT` | 검색 |

## 19.6 watch + tail = 실시간 대시보드

```bash
# 매 2초마다 명령 결과 갱신
watch -n 2 'df -h'

# 색 보존
watch -c -n 1 'systemctl --no-pager status nginx'

# 차이만 강조
watch -d -n 1 'ss -ltn'

# tail 같이
watch -n 5 'tail -n 20 /var/log/syslog'
```

## 19.7 자주 쓰는 한 줄

```bash
# 큰 로그에서 마지막 1만 줄만 빠르게
tail -n 10000 huge.log | less

# 특정 시간 이후 로그
tail -n +1 file | sed -n '/^2026-05-07/,$p'

# 파일이 작성될 때까지 기다렸다가 본문 보기
tail -F /var/log/nginx/error.log | sed '/critical/q'

# 두 로그 합쳐 시간순
sort -m -k1,2 a.log b.log | less

# CSV의 처음 5줄과 마지막 5줄
(head -5; tail -5) < big.csv

# 처음/마지막 동시
head -5 file && echo "..." && tail -5 file

# wc 빠르게 (헤더 빼기)
wc -l < file       # 헤더(==> file <==) 안 나옴

# pv 로 진행률 + 라인 수
pv file | wc -l    # 큰 파일에서 진행률 함께
```

## 19.8 pv — 파이프 뷰어

```bash
sudo apt install pv

pv big.iso > /dev/null         # 처리 속도 표시
cat big.csv | pv | wc -l       # 진행률 + 처리량
pv -L 1m big.iso | nc host 9000  # 1MB/s 제한
gzip -c file | pv -s $(stat -c%s file) > file.gz
```

## 19.9 디버깅 / 실전

### 로그 쪼개서 보기 (tmux/screen 패널)

```bash
# 좌패널
tail -F /var/log/nginx/access.log

# 우패널
tail -F /var/log/nginx/error.log

# 아래 패널
watch -n 2 'ss -lntp'
```

자세한 멀티 세션은 [제26장].

### 매우 큰 파일

```bash
less big.log          # 전체 안 읽음, 페이지 단위
# Page Down 으로 인덱싱 → G 가 한 번 느릴 뿐
```

`less +G` 후 `Ctrl+C` → 끝부터 거꾸로 위로 보기.

다음 챕터: [제20장]

\newpage

---


# 20. diff / patch / tee / xxd

> 차이 보고, 패치 만들고, 출력을 분기시키고, 바이너리도 본다.

## 20.1 diff — 두 파일 비교

```bash
diff a.txt b.txt
diff -u a.txt b.txt          # unified (가장 흔함)
diff -c a.txt b.txt          # context
diff -y a.txt b.txt          # side-by-side
diff -q a.txt b.txt          # 같음/다름만
diff -r dir1/ dir2/          # 디렉토리 재귀
diff -ru dir1/ dir2/
diff --brief -r dir1 dir2    # 어떤 파일이 다른지만
diff -i a b                  # 대소문자 무시
diff -w a b                  # 공백 변화 무시
diff -B a b                  # 빈 줄 무시
diff --color a b             # 컬러 (GNU)
```

### unified diff 형식

```
--- a.txt   2026-05-06
+++ b.txt   2026-05-07
@@ -1,4 +1,4 @@
 unchanged line
-old line
+new line
 another unchanged
```

`-`: 옛 파일, `+`: 새 파일. `@@` 헤더는 줄 위치(`-시작,길이 +시작,길이`).

### 디렉토리 비교

```bash
# 다른 파일들과 그 내용
diff -ru old/ new/

# 다른 파일 이름만
diff -rq old/ new/

# 새 디렉토리에만 있는 파일
diff -rq old/ new/ | grep "^Only in new"
```

### 의미 있는 비교

```bash
# 정렬 차이는 무시
diff <(sort a) <(sort b)

# 공백/순서 무시
diff -wB <(sort a) <(sort b)

# 가공 후 비교
diff <(grep -v '^#' a.conf | sort) <(grep -v '^#' b.conf | sort)
```

`<( )` 는 프로세스 치환. 명령 출력을 임시 파일처럼.

## 20.2 colordiff / icdiff / delta

```bash
sudo apt install colordiff icdiff
colordiff -u a b
icdiff a b           # 깔끔한 side-by-side, 컬러
```

`delta` 는 git diff의 현대화된 페이저:

```bash
# .gitconfig
[core]
    pager = delta
[delta]
    line-numbers = true
    side-by-side = true
```

## 20.3 patch — 차이 적용

```bash
# 패치 만들기
diff -u original.txt modified.txt > my.patch

# 적용
patch < my.patch                   # 한 파일
patch -p1 < big.patch              # 디렉토리 (-p1: 첫 디렉토리 제거)
patch -p0 < flat.patch
patch -R < my.patch                # 되돌리기
patch --dry-run < my.patch         # 시뮬레이션
patch -b < my.patch                # 백업 .orig 생성
patch -F 3 < my.patch              # fuzz factor 3
```

| 옵션 | 의미 |
|------|------|
| `-pN` | 경로에서 N단계 strip |
| `-R` | reverse |
| `-b` | 백업 |
| `-N` | 이미 적용된 패치 무시 |
| `-d DIR` | 작업 디렉토리 |
| `-i FILE` | 입력 파일 (또는 stdin) |
| `--dry-run` | 시뮬 |
| `-F N` | 컨텍스트 fuzz |
| `-l` | 공백 차이 무시 |

### -p 의 의미

패치 안에 `--- a/src/main.c` 라면:

- `-p0` → `a/src/main.c` 그대로
- `-p1` → `src/main.c` (첫 디렉토리 a 제거)
- `-p2` → `main.c`

`git diff` 결과는 보통 `-p1` 로 적용.

### 거부된 hunk

```
patching file foo.c
Hunk #2 FAILED at 23.
1 out of 2 hunks FAILED -- saving rejects to file foo.c.rej
```

`.rej` 파일을 열어 수동으로 머지.

## 20.4 git diff (간단)

```bash
git diff                          # working ↔ index
git diff --cached                 # index ↔ HEAD
git diff HEAD                     # working ↔ HEAD
git diff branch1 branch2          # 두 브랜치
git diff branch1..branch2 -- path
git diff --stat                   # 요약
git diff --no-color | colordiff
git diff --word-diff              # 단어 단위
git diff --check                  # 화이트스페이스 문제만
```

자주 쓰는 외부 도구:

```bash
git difftool          # GUI/CLI 외부 도구로
```

## 20.5 tee — 출력 분기

stdout 으로 보내면서 동시에 파일에도 저장.

```bash
ls | tee out.txt          # 화면 + 파일
ls | tee -a out.txt       # append
ls | tee a.txt b.txt      # 다중 파일
make 2>&1 | tee build.log

# sudo 가 필요한 경로에 쓰기
echo "127.0.0.1 myhost" | sudo tee -a /etc/hosts
```

리다이렉트(`>`)는 셸이 처리하므로 sudo 가 안 듣는다. 그래서 `sudo tee` 를 쓴다.

```bash
# X
sudo echo "..." > /etc/something    # /etc/something 의 권한 부족

# O
echo "..." | sudo tee /etc/something
echo "..." | sudo tee -a /etc/something
```

### tee + 프로세스 치환 (분기 처리)

```bash
make 2>&1 | tee >(grep -i error > errors.log) >(grep -i warn > warns.log) > all.log
```

빌드 출력 한 번에 화면 + 에러 / 경고 / 전체 로그 분리.

## 20.6 xxd / hexdump / od — 바이너리 들여다보기

```bash
xxd file | less
xxd -l 64 file        # 첫 64 바이트
xxd -s 100 -l 32 file # offset 100 부터 32바이트
xxd -c 8 file         # 한 줄 8바이트
xxd -p file           # plain hex (공백 없는)
xxd -r -p hex.txt > out.bin   # 역변환

hexdump -C file       # canonical (16진 + ASCII)
od -A x -t x1z -v file
```

xxd 의 출력 예:

```
00000000: 7f45 4c46 0201 0100 0000 0000 0000 0000  .ELF............
```

ELF 매직(`7F 45 4C 46`) 보임 → ELF 바이너리 확인.

### 자주 쓰는 패턴

```bash
# 파일 매직 확인
xxd -l 16 file

# 임의의 바이너리 안에서 문자열 검색
strings file | sed -n '/ABC/Ip'

# 바이너리 동일 여부
cmp -s a.bin b.bin && echo same

# 작은 차이만 시각화
cmp -l a.bin b.bin | head     # offset, byte1, byte2 (8진)
```

## 20.7 strings — 바이너리에서 문자열 추출

```bash
strings file
strings -n 8 file       # 길이 8 이상
strings binary | sed -n '/version/Ip'
```

## 20.8 vim 의 vimdiff (덤으로)

```bash
vimdiff a.txt b.txt
vim -d a.txt b.txt
```

(이 책에선 vi 제외 대상이지만 비교 도구로 자주 쓰여 언급)

차이 줄 사이 이동: `]c`, `[c`. 머지: `do`, `dp`.

## 20.9 자주 쓰는 한 줄

```bash
# 두 디렉토리 차이
diff -rq dir1 dir2 | sort

# 두 디렉토리에서 같은 이름 다른 내용
diff -rq dir1 dir2 | sed -n '/differ$/p'

# 한쪽에만 있는 파일
diff -rq dir1 dir2 | sed -n '/^Only in /p'

# 두 명령 결과 비교
diff <(cmd1) <(cmd2)

# 변경 전후 백업
cp file file.$(date +%Y%m%d-%H%M%S)
edit file
diff -u file.* file

# unified 패치 만들고 다른 곳에 적용
diff -u v1/ v2/ > update.patch
cd /target/v1
patch -p1 --dry-run < /path/update.patch
patch -p1 < /path/update.patch

# 빌드 로그를 화면 + 파일 + 에러 따로
make 2>&1 | tee build.log | sed -n '/error/Ip' > errors.log
```

다음 챕터: [제21장]

\newpage

---


# 21. 프로세스 — ps, top, htop, pidof, pstree

> 무엇이 돌고 있는지, 얼마나 먹는지, 어디서 왔는지.

## 21.1 ps — 스냅샷

```bash
ps                # 내 셸 자식들만
ps -e             # 전체
ps -ef            # 전체 + full format (UID, PPID 등)
ps aux            # BSD 스타일 (사람 이름, %CPU, %MEM)
ps -ejH           # 트리 형식
ps -eLf           # 스레드까지
ps -p PID         # 특정 PID
ps -C nginx       # 명령 이름으로
ps --ppid PPID    # 부모 기준
ps -u USER        # 사용자
ps -G GROUP       # 그룹
```

### ps aux 컬럼

```
USER  PID %CPU %MEM   VSZ   RSS TTY STAT START TIME COMMAND
```

| 컬럼 | 의미 |
|------|------|
| USER | 소유자 |
| PID | 프로세스 ID |
| %CPU | 누적 CPU |
| %MEM | 메모리 비율 |
| VSZ | 가상 메모리 (KB) |
| RSS | 실 메모리 (KB) |
| TTY | 단말 (`?` = 데몬) |
| STAT | 상태 (R, S, D, Z, T, I 등) |
| START | 시작 시각 |
| TIME | 누적 CPU 시간 |
| COMMAND | 명령 |

### STAT 상태 코드

| 코드 | 의미 |
|------|------|
| R | running 또는 runnable |
| S | sleep (interruptible) |
| D | uninterruptible sleep (보통 디스크/IO) |
| Z | zombie (종료 후 부모가 wait 안 함) |
| T | stopped (Ctrl+Z) |
| I | idle 커널 스레드 |
| `<` | 높은 우선순위 |
| `N` | 낮은 우선순위 |
| `s` | 세션 리더 |
| `+` | 포어그라운드 그룹 |
| `l` | 멀티스레드 |

`D` 가 오래 가면 디스크 / NFS 문제 의심. `Z` 는 부모가 wait()  안 하는 버그.

### 컬럼 직접 지정 (`-o`)

```bash
ps -eo pid,ppid,user,pcpu,pmem,start,etime,cmd
ps -eo pid,user,cmd --sort=-pcpu | head
ps -eo pid,rss,cmd --sort=-rss | head     # 메모리 큰 순
```

| 자주 쓰는 컬럼 | |
|---------------|---|
| `pid` `ppid` | PID, 부모 |
| `pgid` `sid` | 프로세스 그룹/세션 |
| `tid` | 스레드 ID |
| `user` `uid` | 사용자 |
| `pcpu` `pmem` | %CPU, %MEM |
| `vsz` `rss` | 가상/실 메모리 |
| `start` `start_time` | 시작 |
| `etime` `etimes` | 경과 시간 (HH:MM:SS / 초) |
| `time` | CPU 시간 |
| `nlwp` | 스레드 수 |
| `stat` | 상태 |
| `cmd` `comm` `args` | 명령 |
| `wchan` | 대기 함수 (커널) |
| `psr` | 현재 CPU |
| `ni` `pri` | nice / priority |

### 정렬

```bash
ps aux --sort=-rss | head           # 메모리 ↓
ps -eo pid,pcpu,cmd --sort=-pcpu | head
ps -eo pid,etime,cmd --sort=etime  # 오래된 것부터
```

`-` 는 내림차순.

### 트리

```bash
ps -ejH | less
ps -ef --forest | less
pstree -p
pstree -ap | less                  # 명령행 + PID
pstree -u                          # 사용자별
pstree -s PID                      # PID 의 조상
```

## 21.2 pidof / pgrep / pkill

```bash
pidof nginx                # nginx 의 모든 PID
pgrep -fl nginx            # 패턴 + 이름 표시
pgrep -u www-data          # 사용자
pgrep -P PARENT_PID        # 자식만
pgrep -c sshd              # 개수
pgrep -n nginx             # 가장 최근 시작된 것

pkill -HUP nginx
pkill -9 -f 'python myscript'
pkill -u alice
```

| 옵션 | 의미 |
|------|------|
| `-f` | 명령 전체(args) 매칭 |
| `-l` | 이름 표시 |
| `-u U` | 사용자 |
| `-P P` | 부모 PID |
| `-x` | 정확히 일치 |
| `-n` `-o` | 가장 최신/오래된 것만 |
| `-c` | 카운트 |
| `-d D` | 출력 구분자 |

`pgrep`은 `ps | grep` 보다 안전하다(자기 자신 매칭 X).

## 21.3 top — 실시간

```bash
top
top -d 1               # 갱신 간격 1초
top -p PID1,PID2       # 특정 PID
top -u USER            # 사용자
top -H                 # 스레드 단위
top -b -n 1            # batch (스크립트용, 한 번)
```

### 인터랙티브 키

| 키 | 동작 |
|----|------|
| `q` | 종료 |
| `h` | 도움말 |
| `?` | 도움말 |
| `M` | 메모리(RSS) 정렬 |
| `P` | CPU 정렬 |
| `T` | 시간 정렬 |
| `N` | PID 정렬 |
| `R` | 정렬 방향 반전 |
| `c` | 명령 풀 경로 |
| `f` | 컬럼 선택 |
| `o` `O` | 필터 |
| `u` | 사용자 필터 |
| `1` | CPU 코어별 표시 |
| `H` | 스레드 토글 |
| `d` | 갱신 간격 |
| `k` | 시그널 보내기 |
| `r` | nice 값 변경 |
| `W` | 설정 저장 |
| `Z` | 색상 |
| `e` | 메모리 단위 |
| `E` | 상단 메모리 단위 |

### 상단 요약

```
top - 09:30:00 up 5 days,  1:23,  3 users,  load average: 0.20, 0.30, 0.40
Tasks: 234 total,   1 running, 233 sleeping
%Cpu(s):  5.0 us,  2.0 sy,  0.0 ni, 92.0 id,  1.0 wa,  0.0 hi,  0.0 si,  0.0 st
MiB Mem :   8000 total,   1000 free,   5000 used,   2000 buff/cache
MiB Swap:   2000 total,   1500 free,    500 used.   3000 avail Mem
```

| 항목 | 의미 |
|------|------|
| load average | 1/5/15분 평균 실행 큐 |
| us | user CPU |
| sy | system (커널) CPU |
| ni | niced user |
| id | idle |
| wa | I/O wait |
| hi | hardware interrupt |
| si | software interrupt |
| st | stolen (가상화 호스트가 가져감) |

`wa` 가 높으면 디스크/네트워크 병목, `st` 가 높으면 호스트 과부하.

## 21.4 htop — 친절한 top

```bash
sudo apt install htop
htop
htop -u USER
htop -p PID1,PID2
```

화살표/마우스로 직관적 조작. `F1`~`F10` 단축키:

| 키 | 동작 |
|----|------|
| F1 | 도움말 |
| F2 | 설정 |
| F3 | 검색 |
| F4 | 필터 |
| F5 | 트리 보기 |
| F6 | 정렬 |
| F7 | nice ↓ |
| F8 | nice ↑ |
| F9 | kill |
| F10 | 종료 |
| `t` | 트리 토글 |
| `H` | 스레드 토글 |
| `K` | 커널 스레드 |
| `u` | 사용자 필터 |
| `\` | 검색 |
| `s` | strace |
| `l` | lsof |
| `Space` | 프로세스 마크 |

## 21.5 atop / btop / glances — 더 풍부한 모니터

```bash
sudo apt install atop btop glances
atop                    # 시스템 전체 + 디스크/네트워크
atop -r /var/log/atop/atop_20260507  # 과거 기록 재생
btop                    # 컬러풀, 마우스
glances                 # 한 화면에 거의 모든 지표
```

`atop` 은 부팅마다 10분 간격 스냅샷을 자동 저장 → 사후 분석 가능.

## 21.6 nice / renice / ionice / chrt

```bash
nice -n 10 cmd          # nice 10 으로 실행 (낮은 우선순위)
nice -n -5 cmd          # 높은 우선순위 (root)
renice 5 -p PID
renice 5 -u USER
ionice -c 3 -p PID      # idle I/O class
ionice -c 2 -n 7 cmd    # best-effort, 가장 낮은
chrt -f -p 50 PID       # FIFO 50 (실시간) - root
chrt -i 0 cmd           # idle scheduling
```

| 클래스(ionice) | 의미 |
|---|---|
| 1 | real time (root) |
| 2 | best-effort (기본) 0~7 |
| 3 | idle |

CPU nice: -20 (높음) ~ 19 (낮음). 일반 사용자는 0~19 만.

## 21.7 시그널 보내기 — kill

[제22장] 에서 자세히. 빠른 미리보기:

```bash
kill PID            # SIGTERM
kill -9 PID         # SIGKILL (강제)
kill -HUP PID       # 설정 reload
kill -l             # 시그널 목록
```

## 21.8 /proc — 프로세스 내부 들여다보기

```bash
ls /proc/PID
# cmdline cwd environ exe fd/ maps mem net status ...

cat /proc/PID/status     # 메모리/스레드 등 상태
cat /proc/PID/cmdline | tr '\0' ' '; echo
ls -l /proc/PID/exe      # 실행 파일
ls -l /proc/PID/cwd      # 작업 디렉토리
ls /proc/PID/fd          # 열린 파일 디스크립터
cat /proc/PID/limits     # rlimit
cat /proc/PID/maps       # 메모리 맵
cat /proc/PID/stack      # 커널 스택
```

자동화에 매우 유용:

```bash
# nginx 의 작업 디렉토리
readlink /proc/$(pidof nginx | awk '{print $1}')/cwd

# 프로세스가 연 파일들
ls -l /proc/PID/fd/
```

## 21.9 자주 쓰는 한 줄

```bash
# 메모리 먹는 톱 5
ps -eo pid,user,cmd,%mem,rss --sort=-rss | head -6

# CPU 먹는 톱 5
ps -eo pid,user,cmd,%cpu --sort=-pcpu | head -6

# 가장 오래 산 프로세스
ps -eo pid,etime,cmd --sort=-etime | head

# 좀비
ps -eo pid,ppid,stat,cmd | sed -n '/[Zz]/p'

# 데몬화된 셸 자식 (parent=1)
ps -eo pid,ppid,cmd | awk '$2==1'   # awk 빠질 때
ps --ppid 1 -o pid,cmd

# 특정 사용자
ps -u alice -o pid,cmd,%cpu,%mem

# 좀비 부모 죽이기
ZOMBIES=$(ps -eo pid,stat | sed -n '/Z/p' | awk '{print $1}')
for z in $ZOMBIES; do
  ppid=$(ps -o ppid= -p "$z")
  echo "zombie $z parent $ppid"
done

# nohup 좀비 정리
pkill -9 -f some_pattern

# 메모리 누수 모니터
watch -n 5 "ps -p $PID -o pid,vsz,rss,cmd"
```

다음 챕터: [제22장]

\newpage

---


# 22. kill 과 시그널

> 프로세스에 보내는 메시지. SIGTERM 이 정중하게, SIGKILL 이 사정없이.

## 22.1 시그널 카탈로그

`kill -l` 로 목록을 본다. 자주 쓰는 것들:

| 번호 | 이름 | 의미 / 기본 동작 |
|------|------|-------------------|
| 1 | SIGHUP | 단말 끊김 / 설정 reload (관례) |
| 2 | SIGINT | 인터럽트 (Ctrl+C) |
| 3 | SIGQUIT | 종료 + core dump (Ctrl+\) |
| 6 | SIGABRT | abort() |
| 9 | SIGKILL | **즉시 종료** (잡을 수 없음) |
| 14 | SIGALRM | 알람 타이머 |
| 15 | SIGTERM | 정중한 종료 (기본) |
| 17 | SIGCHLD | 자식 종료 알림 |
| 18 | SIGCONT | 계속 |
| 19 | SIGSTOP | **정지** (잡을 수 없음) |
| 20 | SIGTSTP | Ctrl+Z 로 정지 |
| 23 | SIGURG | 긴급 데이터 |
| 28 | SIGWINCH | 창 크기 변경 |
| 30/10/16 | SIGUSR1 | 사용자 정의 1 |
| 31/12/17 | SIGUSR2 | 사용자 정의 2 |

번호는 아키텍처마다 약간 다름. 이름으로 부르는 게 안전 (`-HUP`, `-TERM`, `-9`).

### 잡을 수 없는 시그널

- `SIGKILL (9)` — 즉시 종료. 핸들러도, 무시도 불가.
- `SIGSTOP (19)` — 즉시 정지. 동일.

다른 시그널은 모두 핸들러로 가로채거나 무시 가능.

## 22.2 kill 명령

```bash
kill PID                  # SIGTERM (기본)
kill -9 PID               # SIGKILL
kill -HUP PID             # 이름으로
kill -SIGHUP PID
kill -s HUP PID
kill -l                   # 시그널 목록
kill -l 9                 # 9 → KILL
kill -l KILL              # KILL → 9

kill -0 PID               # 시그널 안 보내고 존재만 확인 (권한도 검사)
```

다중:

```bash
kill -9 1234 1235 1236
kill -- -PGID             # 음수 → 프로세스 그룹 (포어그라운드 작업 통째)
```

## 22.3 정중한 종료 흐름

```bash
# 1) 정중하게 (TERM)
kill PID

# 2) 잠깐 기다림
sleep 5

# 3) 살아있으면 강제 (KILL)
kill -0 PID 2>/dev/null && kill -9 PID
```

루프로:

```bash
graceful_kill() {
  local pid=$1
  kill "$pid" 2>/dev/null || return
  for i in 1 2 3 4 5; do
    kill -0 "$pid" 2>/dev/null || return
    sleep 1
  done
  kill -9 "$pid" 2>/dev/null
}
```

DB / 큐 같은 데몬에 SIGKILL 남발하면 데이터 손상 가능. 거의 항상 SIGTERM 먼저.

## 22.4 killall — 이름으로

```bash
killall nginx                 # 모두 SIGTERM
killall -9 nginx              # SIGKILL
killall -u alice firefox      # 사용자 한정
killall -i nginx              # 프롬프트
killall --older-than 1h cmd   # 1시간 이상 산 것만
killall --younger-than 5m cmd
killall -e LongCommandName    # 정확히 일치 (15자 잘림 회피)
killall -r '^my-.*'           # 정규식
killall -s SIGUSR1 nginx
killall -w nginx              # 종료까지 wait
killall -g GROUP              # 프로세스 그룹
```

> Solaris 의 `killall` 은 모든 프로세스 죽이는 다른 명령. 리눅스만 안전.

## 22.5 pkill — 패턴

```bash
pkill nginx               # 이름 매칭
pkill -f 'python app.py'  # 명령 전체
pkill -u alice            # 사용자
pkill -P PARENT           # 부모 자식만
pkill -SIGHUP nginx
pkill -9 -f long_pattern
```

`pgrep` 으로 미리 확인하는 습관:

```bash
pgrep -fla 'python app.py'
# OK 면
pkill -f 'python app.py'
```

## 22.6 시그널을 활용한 데몬 운영

| 시그널 | 흔한 용도 |
|--------|-----------|
| SIGHUP | 설정 reload (nginx, sshd, syslogd 다수) |
| SIGUSR1 | 로그 회전 / 디버그 토글 |
| SIGUSR2 | 핫 재시작 / 상태 덤프 |
| SIGTERM | 정중한 종료 |
| SIGINT | 인터랙티브 인터럽트 (Ctrl+C) |
| SIGQUIT | 코어 덤프 + 종료 |
| SIGWINCH | nginx graceful 종료 (worker만) |

예:

```bash
# nginx 설정 다시
sudo nginx -t && sudo nginx -s reload
# = sudo kill -HUP $(cat /var/run/nginx.pid)

# nginx 핫 재시작 (구버전 → 새버전)
sudo kill -USR2 $(cat /var/run/nginx.pid)
sudo kill -WINCH $(cat /var/run/nginx.pid.oldbin)   # 옛 worker 종료
sudo kill -QUIT $(cat /var/run/nginx.pid.oldbin)    # 옛 master 종료
```

데몬마다 시그널 정의가 다르다. 매뉴얼 확인 (`man 8 nginx`, `man 8 sshd`).

## 22.7 셸 트랩 — 시그널을 받아서 정리

```bash
#!/bin/bash
cleanup() {
  echo "정리 중..."
  rm -f /tmp/lockfile
}
trap cleanup EXIT INT TERM

touch /tmp/lockfile
# ... 작업 ...
sleep 1000
```

`trap` 옵션:

```bash
trap '' SIGINT       # 무시 (빈 명령)
trap - SIGINT        # 기본 동작 복원
trap 'echo bye' EXIT
trap 'kill -- -$$' EXIT   # 자식 그룹 통째 정리
```

| 의사 시그널 | 의미 |
|-------------|------|
| EXIT | 스크립트 종료 시 |
| ERR | 어느 명령이 0 아닌 종료 |
| DEBUG | 매 명령 직전 |
| RETURN | 함수/소스 반환 |

`set -e` 와 `trap ... ERR` 로 견고한 스크립트.

## 22.8 Ctrl 키와 시그널

| 키 | 시그널 |
|----|--------|
| Ctrl+C | SIGINT |
| Ctrl+\ | SIGQUIT (core dump) |
| Ctrl+Z | SIGTSTP (정지) |

정지된 작업:

```bash
fg          # 다시 포어
bg          # 백그라운드 진행
jobs        # 목록
kill %1     # 작업 1 종료
kill -CONT %1   # 다시 진행
disown %1   # 셸 종료해도 살아남음
```

자세한 잡 컨트롤은 [제27장].

## 22.9 권한 / 함정

- `kill` 은 동일 사용자(또는 root) 의 프로세스만 가능
- `kill -1`, `kill -- -PGID` 처럼 음수 PGID 는 **프로세스 그룹 전체**
- `kill -- -1` (PID -1) → 자기 자신과 init 빼고 모든 프로세스에 시그널 (위험)
- 좀비(`Z`) 프로세스에 `kill -9` 안 통함. 부모 프로세스를 죽여야 reaped

## 22.10 자주 쓰는 한 줄

```bash
# nginx 부드럽게 reload
sudo systemctl reload nginx
# = sudo kill -HUP $(cat /run/nginx.pid)

# 종속된 자식 다 종료
pkill -P PARENT_PID

# 패턴으로 모두 잡기
pgrep -fla python
pkill -9 -f 'python.*broken'

# Idle 상태 SSH 세션 종료
who -u                       # 사용자 / TTY / IDLE / PID
sudo kill -HUP $(who -u | sed -n '/old/{s/.* //p}')

# 가장 메모리 큰 사용자 프로세스 즉시 종료 (위험)
ps -u alice --sort=-rss -o pid= | head -1 | xargs kill

# 시그널을 받아 graceful shutdown 하는 스크립트
cat > worker.sh <<'EOF'
#!/bin/bash
trap 'echo "stopping"; STOP=1' TERM INT
STOP=0
while [ "$STOP" = 0 ]; do
  echo "tick $(date)"
  sleep 1
done
echo "bye"
EOF
chmod +x worker.sh
./worker.sh &
PID=$!
sleep 3
kill $PID    # → "stopping" 출력 후 정상 종료
```

다음 챕터: [제23장]

\newpage

---


# 23. systemd 와 systemctl

> 부팅, 서비스, 타이머, 마운트, 네트워크. 현대 리눅스 init.

## 23.1 큰 그림

systemd 는 PID 1 init 이자 서비스 매니저. 거의 모든 것이 **유닛(unit)** 으로 모델링됨:

| 유닛 종류 | 확장자 | 의미 |
|-----------|--------|------|
| service | .service | 서비스 데몬 |
| socket | .socket | 소켓 활성화 |
| timer | .timer | cron 대체 |
| target | .target | 그룹 (runlevel 같음) |
| mount | .mount | 마운트 포인트 |
| automount | .automount | 자동 마운트 |
| path | .path | 파일/디렉토리 변화 트리거 |
| device | .device | 장치 |
| swap | .swap | 스왑 |
| slice | .slice | cgroup 슬라이스 |
| scope | .scope | 외부 프로세스 그룹 |

유닛 파일 위치:

| 경로 | 용도 |
|------|------|
| `/usr/lib/systemd/system/` | 패키지 제공 (편집 X) |
| `/etc/systemd/system/` | 관리자 작성 / 오버라이드 |
| `/run/systemd/system/` | 런타임 (재부팅 시 사라짐) |
| `~/.config/systemd/user/` | 사용자 단위 |

## 23.2 systemctl 기초

```bash
systemctl status                 # 시스템 전체 상태
systemctl                        # 활성 유닛 목록
systemctl list-units --type=service
systemctl list-units --failed
systemctl list-unit-files        # 모든 유닛 파일 (활성/비활성)
systemctl list-dependencies sshd.service

systemctl status sshd
systemctl is-active sshd
systemctl is-enabled sshd
systemctl is-failed sshd
```

### 서비스 제어

```bash
sudo systemctl start nginx
sudo systemctl stop nginx
sudo systemctl restart nginx
sudo systemctl reload nginx           # 설정 재적용 (지원 시)
sudo systemctl reload-or-restart nginx
sudo systemctl try-restart nginx      # 실행 중일 때만
sudo systemctl kill -s HUP nginx      # 시그널 직접
```

### 부팅 시 활성화

```bash
sudo systemctl enable nginx           # 부팅 시 시작
sudo systemctl enable --now nginx     # + 즉시 시작
sudo systemctl disable nginx
sudo systemctl disable --now nginx
sudo systemctl mask nginx             # 시작도 못 하게 잠금
sudo systemctl unmask nginx
```

`mask` 는 심볼릭 링크를 `/dev/null` 로 → 어떤 의존성도 시작 못 함.

### 새 유닛 인식

```bash
sudo systemctl daemon-reload          # 유닛 파일 변경 후 필수
```

## 23.3 유닛 파일 작성 — 서비스

`/etc/systemd/system/myapp.service`:

```ini
[Unit]
Description=My App
Documentation=https://example.com/myapp
After=network-online.target
Wants=network-online.target
Requires=postgresql.service

[Service]
Type=simple
User=app
Group=app
WorkingDirectory=/opt/myapp
EnvironmentFile=-/etc/myapp.env
Environment=NODE_ENV=production
ExecStart=/usr/bin/node /opt/myapp/server.js
ExecReload=/bin/kill -HUP $MAINPID
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal
LimitNOFILE=65536
TimeoutStopSec=30

# 보안 강화
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/lib/myapp /var/log/myapp

[Install]
WantedBy=multi-user.target
```

활성화:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now myapp
sudo systemctl status myapp
```

### Type 종류

| Type | 의미 |
|------|------|
| simple | ExecStart 가 메인 프로세스 (기본) |
| exec | simple + 자식 exec 후 ready |
| forking | ExecStart 가 fork 후 부모 종료 (전통 데몬) |
| oneshot | 한 번 실행 (스크립트). 보통 RemainAfterExit=yes 와 |
| notify | 프로세스가 sd_notify(READY=1) 보냄 |
| dbus | DBus 이름 등장 시 ready |
| idle | 다른 작업 끝난 후 시작 |

### Restart 정책

| 값 | 의미 |
|----|------|
| no | 안 함 |
| always | 항상 |
| on-success | 정상 종료 시도 다시 |
| on-failure | 비정상(에러/시그널) |
| on-abnormal | 시그널/타임아웃 |
| on-watchdog | 워치독 만료 |
| on-abort | abort 시그널 |

대부분 `on-failure` 또는 `always`.

### 보안 옵션 (자주 쓰는)

| 옵션 | 의미 |
|------|------|
| `NoNewPrivileges=true` | setuid 등 권한 상승 금지 |
| `ProtectSystem=strict` | /usr, /boot, /etc 읽기 전용 |
| `ProtectHome=true` | /home, /root, /run/user 안 보임 |
| `PrivateTmp=true` | /tmp 격리 |
| `PrivateDevices=true` | /dev 거의 비움 |
| `ProtectKernelTunables=true` | /proc/sys, /sys 읽기 전용 |
| `ProtectKernelModules=true` | 모듈 로드 금지 |
| `ProtectKernelLogs=true` | dmesg 차단 |
| `ProtectControlGroups=true` | cgroups 보호 |
| `ReadWritePaths=` | 쓰기 허용 경로 |
| `CapabilityBoundingSet=` | 허용 capability |
| `RestrictAddressFamilies=` | 소켓 종류 |
| `SystemCallFilter=@system-service` | seccomp |
| `MemoryMax=` | 메모리 한계 |
| `CPUQuota=` | CPU 한계 |
| `LimitNOFILE=` | rlimit |

`systemd-analyze security myapp` 으로 점수 확인.

## 23.4 오버라이드 — drop-in

패키지 유닛은 건드리지 말고 오버라이드.

```bash
sudo systemctl edit nginx
```

`/etc/systemd/system/nginx.service.d/override.conf` 가 만들어짐. 편집 후 자동으로 daemon-reload.

```ini
[Service]
LimitNOFILE=200000
Environment=NGINX_WORKER_CONNECTIONS=4096
```

전체 교체는:

```bash
sudo systemctl edit --full nginx     # 전체 복제 후 편집
sudo systemctl revert nginx          # 오버라이드 모두 제거
```

## 23.5 의존성

```ini
[Unit]
After=network.target              # 시작 순서 (이후에)
Before=ssh.service
Requires=foo.service              # foo 가 실패하면 같이 실패
Wants=foo.service                 # 약한 의존 (foo 실패 무관)
BindsTo=foo.service               # foo 죽으면 같이 죽음
PartOf=foo.service                # foo restart 시 같이
Conflicts=baz.service             # 동시 실행 안 됨
```

### target

전통 runlevel 대체:

| target | 의미 |
|--------|------|
| `default.target` | 기본 (보통 graphical 또는 multi-user) |
| `multi-user.target` | 텍스트 모드 |
| `graphical.target` | 데스크탑 |
| `rescue.target` | 단일 사용자 |
| `emergency.target` | 최소 |
| `reboot.target`, `poweroff.target`, `halt.target` | 종료 |
| `network.target`, `network-online.target` | 네트워크 |

```bash
systemctl get-default
sudo systemctl set-default multi-user.target
sudo systemctl isolate rescue.target       # 즉시 전환
```

## 23.6 systemd 타이머 — cron 대체

`/etc/systemd/system/backup.service`:

```ini
[Unit]
Description=Daily backup
[Service]
Type=oneshot
ExecStart=/usr/local/bin/backup.sh
User=backup
```

`/etc/systemd/system/backup.timer`:

```ini
[Unit]
Description=Daily backup at 03:00

[Timer]
OnCalendar=daily               # 또는 *-*-* 03:00:00
Persistent=true                # 못 돌면 다음 부팅 후 따라잡기
RandomizedDelaySec=15m

[Install]
WantedBy=timers.target
```

활성:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now backup.timer
systemctl list-timers
```

### OnCalendar 표현

```
minutely
hourly
daily
weekly
monthly

Mon..Fri *-*-* 09:00:00
*-*-* 02:00,14:00:00
2026-05-* 18:30
*:0/15                # 15분마다
```

`systemd-analyze calendar 'Mon *-*-* 09:00'` 으로 다음 발사 시각 확인.

### cron vs timer

| 기능 | cron | systemd timer |
|------|------|---------------|
| 의존성 | 없음 | After=, Wants= 풍부 |
| 로그 | mail / 직접 | journald 자동 |
| 누락 시 catch-up | 없음 | `Persistent=true` |
| 격리 | 없음 | service 의 모든 보안 옵션 |
| 표현력 | 단순 cron | 풍부 |
| 복잡도 | 낮음 | 약간 높음 |

새 시스템은 timer 권장. 경량 호스트는 cron 도 OK ([제25장]).

## 23.7 socket / path 활성화

### 소켓 활성화

```ini
# nc.socket
[Socket]
ListenStream=12345
Accept=true
[Install]
WantedBy=sockets.target
```

```ini
# nc@.service (Accept=true 면 인스턴스화)
[Service]
ExecStart=/usr/bin/cat
StandardInput=socket
```

요청이 오면 systemd 가 받고, 그때 서비스를 실행.

### path 활성화

```ini
# myapp.path
[Path]
PathChanged=/etc/myapp/config.yml
Unit=myapp-reload.service

[Install]
WantedBy=multi-user.target
```

파일 변화 → 서비스 트리거.

## 23.8 사용자 단위 (--user)

루트 권한 없이 자기 사용자 영역에서:

```bash
mkdir -p ~/.config/systemd/user
nano ~/.config/systemd/user/syncthing.service
systemctl --user daemon-reload
systemctl --user enable --now syncthing
systemctl --user status syncthing
journalctl --user -u syncthing
```

세션 종료 후에도 유지하려면:

```bash
loginctl enable-linger $USER
```

## 23.9 자원 제한 — cgroup

`systemctl set-property` 로 즉시 적용:

```bash
sudo systemctl set-property myapp MemoryMax=512M
sudo systemctl set-property myapp CPUQuota=50%
sudo systemctl set-property myapp TasksMax=200
```

`/etc/systemd/system/myapp.service.d/50-limits.conf` 에 영구 저장됨.

```bash
systemd-cgtop      # 슬라이스/서비스별 사용량 (top 처럼)
systemd-cgls       # cgroup 트리
```

## 23.10 종합 명령어 모음

```bash
# 부팅 시간 / 어디서 느린가
systemd-analyze
systemd-analyze blame
systemd-analyze critical-chain
systemd-analyze plot > boot.svg

# 의존성
systemctl list-dependencies multi-user.target
systemctl list-dependencies --reverse nginx

# 서비스 환경 변수
systemctl show -p Environment myapp

# 유닛 파일 출처
systemctl cat myapp

# 유닛 파일 새로 만들 때 검증
sudo systemd-analyze verify /etc/systemd/system/myapp.service

# 이미 실행 중인 명령에서 transient 서비스 만들기
systemd-run --user --scope -- htop
systemd-run --unit=mybg --remain-after-exit -- /usr/local/bin/long-task.sh

# 한 번만 (timer 처럼)
systemd-run --on-active=10m --unit=remind /usr/bin/notify-send "10분 됐어요"

# 종료 / 재부팅 / 절전
sudo systemctl reboot
sudo systemctl poweroff
sudo systemctl suspend
sudo systemctl hibernate
sudo systemctl rescue

# 부팅 메시지
sudo systemctl status -l
journalctl -b           # 이번 부팅
journalctl -b -1        # 직전 부팅
```

## 23.11 자주 만나는 함정

| 증상 | 원인 / 대처 |
|------|-------------|
| `daemon-reload` 안 함 | 유닛 변경 후 매번 |
| `Restart=always` 인데 자꾸 죽음 | `RestartSec=` 가 너무 짧아 메모리 폭주 가능, 로그 확인 |
| 환경변수 로드 안 됨 | `EnvironmentFile=`, KEY=VALUE 형식 (export X) |
| 작업 디렉토리 이상 | `WorkingDirectory=` 명시 |
| 권한 부족 | User/Group, ReadWritePaths 점검 |
| 부팅 시 net 미준비 | `After=network-online.target`, `Wants=network-online.target` |
| timer 가 안 돌아감 | `enable --now backup.timer` 했는지 |
| `Active: failed` | `journalctl -u myapp -n 50` |

다음 챕터: [제24장]

\newpage

---


# 24. journalctl — 로그 조회

> systemd 의 로그 데이터베이스. 시간/유닛/PID/우선순위 다 색인됨.

## 24.1 기본

```bash
journalctl                       # 전체 (오래된 것부터)
journalctl -e                    # 끝으로 점프
journalctl -r                    # 최근부터 거꾸로
journalctl -n 50                 # 마지막 50줄
journalctl -f                    # follow (tail -f 처럼)
journalctl --no-pager            # 페이저 안 거침
journalctl -k                    # 커널 로그 (dmesg 동등)
journalctl -b                    # 이번 부팅
journalctl -b -1                 # 직전 부팅
journalctl --list-boots
```

## 24.2 필터

```bash
# 유닛
journalctl -u nginx
journalctl -u nginx -u php-fpm
journalctl -u 'nginx*'           # 글로브

# 사용자 단위
journalctl --user -u syncthing
journalctl _UID=1000

# 우선순위 (syslog level)
journalctl -p err
journalctl -p warning..err

# 시간
journalctl --since "2026-05-07 09:00:00"
journalctl --since "1 hour ago"
journalctl --since today
journalctl --since yesterday --until "today 09:00"
journalctl --since "10min ago"

# PID / 실행파일
journalctl _PID=1234
journalctl _COMM=sshd
journalctl /usr/bin/python3      # 경로

# 정확한 키
journalctl _SYSTEMD_UNIT=nginx.service _UID=33
```

`journalctl -F _COMM` 같이 `-F` 로 어떤 값들이 있는지 확인.

### 우선순위 레벨

| 번호 | 이름 | 약자 |
|------|------|------|
| 0 | emerg | emerg |
| 1 | alert | alert |
| 2 | crit | crit |
| 3 | err | err |
| 4 | warning | warning |
| 5 | notice | notice |
| 6 | info | info |
| 7 | debug | debug |

```bash
journalctl -p 3        # err 이상
journalctl -p err
```

## 24.3 출력 포맷

```bash
journalctl -o short              # 기본
journalctl -o short-iso          # ISO 시간
journalctl -o short-precise      # 마이크로초
journalctl -o cat                # 메시지만
journalctl -o json               # JSON
journalctl -o json-pretty
journalctl -o verbose            # 모든 필드
journalctl -o export             # 직렬화 (백업)
```

타임스탬프 ISO (스크립트용):

```bash
journalctl -u nginx -o short-iso --since '1h ago'
```

JSON + jq:

```bash
journalctl -u sshd -o json --since '1h ago' | jq -c '{t:.__REALTIME_TIMESTAMP,m:.MESSAGE}'
```

## 24.4 follow + 필터

```bash
# 실시간 nginx 에러
journalctl -fu nginx -p err

# 모든 ssh 로그인 시도
journalctl -fu ssh

# 부팅 후 첫 에러부터 따라가기
journalctl -fb -p err
```

## 24.5 디스크 사용 / 정리

```bash
journalctl --disk-usage
journalctl --vacuum-time=2weeks
journalctl --vacuum-size=500M
journalctl --vacuum-files=10
```

`/etc/systemd/journald.conf`:

```
[Journal]
Storage=persistent
SystemMaxUse=2G
SystemKeepFree=500M
SystemMaxFileSize=200M
MaxRetentionSec=2week
ForwardToSyslog=no
Compress=yes
Seal=yes
```

변경 후:

```bash
sudo systemctl restart systemd-journald
```

## 24.6 영구 저장 / 일시 저장

기본은 배포판마다 다르다. `/var/log/journal` 디렉토리 존재 = 영구 저장.

```bash
sudo mkdir -p /var/log/journal
sudo systemd-tmpfiles --create --prefix /var/log/journal
sudo systemctl restart systemd-journald
```

이제 재부팅을 해도 로그 보존.

## 24.7 부팅 분석

```bash
journalctl -b --list-boots         # 모든 부팅 목록 (-1, -2...)
journalctl -b -1                   # 직전 부팅
journalctl -b 2026-05-07           # 날짜 ID
journalctl -b ID                   # boot ID

# 이번 부팅의 첫 에러
journalctl -b -p err

# dmesg 동등
journalctl -k
journalctl -k -b -1                # 직전 부팅 커널 로그
```

## 24.8 쿼리 결합

```bash
# 어제 09:00~10:00 사이 ssh 인증 실패
journalctl -u ssh \
  --since "yesterday 09:00" --until "yesterday 10:00" \
  -g "Failed password"          # -g = grep (정규식)

# 특정 사용자의 로그
journalctl _UID=1000 --since today

# 같은 binary 의 모든 인스턴스
journalctl _COMM=python3 -p err -b
```

`-g` (또는 `--grep`) 은 메시지 정규식 검색 (이 책 grep 제외 규칙 무관 — journalctl 옵션).

## 24.9 다른 호스트 로그 가져오기

```bash
# 호스트의 journal 을 USB 등으로 떠 와서
journalctl --file /run/log/journal/HOSTID/system.journal

# 디렉토리째
journalctl --directory=/mnt/usb/journal
```

## 24.10 export / merge

```bash
# 백업
sudo journalctl -o export > journal.export

# 머지된 다른 머신 로그 (rsync, scp 로 모은 후)
journalctl --merge --directory=/mnt/all/journal
```

## 24.11 dmesg 와 관계

`dmesg` 는 커널 링 버퍼. 일부 배포판에서 일반 사용자가 못 봄 (`kernel.dmesg_restrict=1`). `journalctl -k` 가 권한 친화적.

```bash
sudo dmesg -wH         # H=human, w=watch
sudo dmesg --level=err
sudo dmesg --since '5 min ago'
```

## 24.12 자주 쓰는 한 줄

```bash
# 마지막 부팅 후 실패한 서비스
systemctl --failed
journalctl -b -p err -t systemd

# 가장 최근 ssh 로그인
journalctl -u ssh -g 'Accepted' --since today

# 메모리 OOM 발생
journalctl -k -g 'Out of memory'

# nginx 5xx 만 (access 로그가 journal 에 가는 경우만)
journalctl -u nginx --since today -g ' (5[0-9][0-9]) '

# 직전 부팅이 비정상 종료였는지
journalctl -b -1 -p crit

# 디스크 사용량 큰 호스트 정리
journalctl --vacuum-time=1week
```

## 24.13 주의

- 시간대: 시스템 TZ 기준. UTC 보고 싶으면 `TZ=UTC journalctl ...`
- `--user` 와 시스템 journal 은 분리
- 컨테이너/스냅 안에서는 자체 journal 사용
- `Seal=yes` (FSS) 는 무결성 검증, 운영용으로만
- 큰 시스템에서 journal 용량 폭주 → vacuum / 회전 정책 필수

## 24.14 syslog 와 공존

전통 `/var/log/syslog`, `/var/log/messages` 는 `rsyslog` 가 채운다. 많은 배포판에서 journald + rsyslog 동시 동작:

```
journald → rsyslog → /var/log/{syslog, auth.log, ...}
```

`/etc/rsyslog.conf` 에서 어디로 보낼지 결정. 원격으로 forward 하려면 `omfwd`/`omtcp`. 자세한 건 별도 책의 영역.

다음 챕터: [제25장]

\newpage

---


# 25. cron 과 at — 일정 실행

> 정기 실행은 cron / systemd timer, 일회성은 at.

## 25.1 cron 개요

`cron` 데몬이 `/etc/cron*` 과 사용자 crontab 을 읽어 일정에 맞춰 명령 실행.

| 위치 | 설명 |
|------|------|
| `/etc/crontab` | 시스템 전역 (사용자 필드 포함) |
| `/etc/cron.d/*` | 추가 시스템 cron 파일 |
| `/etc/cron.{hourly,daily,weekly,monthly}/` | 스크립트 디렉토리 |
| `/var/spool/cron/crontabs/USER` (Debian) | 사용자별 |
| `/var/spool/cron/USER` (RHEL) | 사용자별 |

## 25.2 crontab 명령

```bash
crontab -l            # 내 crontab 출력
crontab -e            # 편집 (EDITOR=vim 등)
crontab -r            # 삭제 (조심)
crontab file          # 파일에서 통째로 적용
crontab -u USER -l    # 다른 사용자 (root)
crontab -u USER -e

# 정의 검증
crontab -l | head      # 내 것 확인
sudo run-parts --test /etc/cron.daily   # 어떤 게 돌까 미리 보기 (debian)
```

## 25.3 cron 표현

```
* * * * * 명령
│ │ │ │ │
│ │ │ │ └ 요일 (0-6, 일=0 또는 7)
│ │ │ └── 월   (1-12)
│ │ └──── 일   (1-31)
│ └────── 시   (0-23)
└──────── 분   (0-59)
```

| 표기 | 의미 |
|------|------|
| `*` | 모두 |
| `5` | 정확히 5 |
| `*/5` | 5분 단위 |
| `0,15,30,45` | 목록 |
| `9-17` | 범위 |
| `9-17/2` | 범위 + step |
| `MON-FRI` | 요일 이름 (일부 cron) |
| `JAN,JUL` | 월 이름 |

### 자주 쓰는 패턴

```cron
# 매분
* * * * * cmd

# 5분마다
*/5 * * * * cmd

# 매시 0분
0 * * * * cmd

# 매일 03:00
0 3 * * * cmd

# 평일 09:00
0 9 * * 1-5 cmd

# 매주 일요일 04:30
30 4 * * 0 cmd

# 매월 1일 02:00
0 2 1 * * cmd

# 한 시간에 두 번 (0분, 30분)
0,30 * * * * cmd

# 업무 시간 5분마다
*/5 9-17 * * 1-5 cmd
```

### 특수 문자열 (대부분 cron 지원)

```
@reboot      cmd       # 부팅 시 한 번
@yearly      cmd       # 0 0 1 1 *
@monthly     cmd
@weekly      cmd
@daily       cmd
@hourly      cmd
```

## 25.4 환경 / PATH 함정

cron 의 환경은 매우 작다 (보통 PATH=/usr/bin:/bin). 명시적으로:

```cron
SHELL=/bin/bash
PATH=/usr/local/bin:/usr/bin:/bin
HOME=/home/seunghwa
LANG=C.UTF-8
MAILTO=ops@example.com

0 3 * * * /usr/local/bin/backup.sh
```

또는 명령에서 절대경로 사용 + 스크립트 첫 줄에서 환경 로드:

```bash
#!/bin/bash
source /etc/profile.d/myenv.sh
exec /usr/local/bin/backup
```

## 25.5 출력 / 메일 / 로그

cron 은 stdout/stderr 를 모아 사용자 메일로 보낸다. 메일 인프라가 없다면 직접 리다이렉트.

```cron
# 화면 출력 다 버리기
0 3 * * * /usr/local/bin/backup.sh > /dev/null 2>&1

# 로그 파일에 추가
0 3 * * * /usr/local/bin/backup.sh >> /var/log/backup.log 2>&1

# stdout 만 무시, 에러는 메일로
0 3 * * * /usr/local/bin/backup.sh > /dev/null

# 실패 시에만 알림 (chronic 사용)
sudo apt install moreutils
0 3 * * * chronic /usr/local/bin/backup.sh
# chronic = 실패시에만 출력 노출
```

cron 자체 로그:

```bash
sudo journalctl -t CRON
sudo journalctl -u cron -f
sudo grep CRON /var/log/syslog
```

## 25.6 안전한 cron 스크립트 패턴

```bash
#!/bin/bash
set -euo pipefail
PATH=/usr/local/bin:/usr/bin:/bin
LOG=/var/log/myjob.log
LOCK=/var/run/myjob.lock

exec 9>"$LOCK"
flock -n 9 || { echo "$(date): already running" >> "$LOG"; exit 0; }

{
  echo "=== start $(date -Iseconds) ==="
  # 실제 작업
  /usr/local/bin/backup.sh
  echo "=== end $(date -Iseconds) ==="
} >> "$LOG" 2>&1
```

- `flock` 으로 중복 실행 방지
- `set -euo pipefail` 로 사일런트 실패 차단
- 절대경로 사용
- 로그 명시적 리다이렉트

## 25.7 시스템 cron 디렉토리

```bash
ls /etc/cron.daily/
# logrotate, apt-update, ...
```

이 디렉토리에 실행 가능한 스크립트를 넣으면 매일 한 번 자동 실행. 실행 시각은 `/etc/crontab` (debian) 또는 `/etc/anacrontab` (RHEL) 에서 결정.

```bash
sudo cp my-cleanup.sh /etc/cron.daily/
sudo chmod +x /etc/cron.daily/my-cleanup.sh
sudo run-parts --test /etc/cron.daily   # 미리 보기
```

스크립트 이름에 점(`.`) 안 됨 (run-parts 가 무시).

## 25.8 anacron — 꺼져있는 시간 보충

랩탑/잘 안 돌아가는 머신용. 정해진 시간에 안 돌았으면 켜진 직후 따라잡음.

`/etc/anacrontab`:

```
# period delay job-id command
1       5       cron.daily      run-parts --report /etc/cron.daily
7       25      cron.weekly     run-parts --report /etc/cron.weekly
@monthly 45     cron.monthly    run-parts --report /etc/cron.monthly
```

## 25.9 at — 일회성 예약

```bash
sudo apt install at
sudo systemctl enable --now atd

at 09:00 tomorrow
at> ls -l /tmp > /tmp/list.txt
at> <Ctrl+D>

at now + 5 minutes
at 16:30
at 'next Monday'
at -f script.sh 14:00

atq                 # 큐 목록
atrm 3              # 작업 3 취소
at -c 3             # 작업 3 내용
```

| 시각 표기 | 의미 |
|-----------|------|
| `HH:MM` | 오늘 (이미 지났으면 내일) |
| `HH:MM AM/PM` | |
| `noon`, `midnight`, `teatime` | 12:00, 00:00, 16:00 |
| `tomorrow` | |
| `MMDDYY`, `MM/DD/YY`, `DD.MM.YY` | |
| `now + 1 hour` | |
| `next Mon`, `next week` | |

at 도 cron 처럼 PATH 빈약 → 절대경로 추천.

## 25.10 batch — 부하 낮을 때 실행

```bash
batch
batch> heavy-job.sh
batch> <Ctrl+D>
```

시스템 load 가 낮을 때 (`atq.conf` 임계값) 실행.

## 25.11 cron vs systemd timer 결정

| 상황 | 추천 |
|------|------|
| 단순한 한두 줄 | cron |
| 다중 의존성 / 격리 / 한계 자원 | timer |
| 누락 시 catch-up 필요 | timer (`Persistent=true`) 또는 anacron |
| 부팅 직후 한 번 | timer (`OnBootSec=`) 또는 `@reboot` cron |
| 컨테이너 안 | 보통 외부 cron / k8s CronJob |
| 기존 cron 자산이 많음 | 그대로 cron |

## 25.12 자주 쓰는 한 줄 / 스니펫

```bash
# 매일 03:00 백업, 실패만 메일
MAILTO=ops@example.com
0 3 * * * chronic /usr/local/bin/backup.sh

# 5분마다 상태 체크 + 알림
*/5 * * * * /usr/local/bin/healthcheck.sh || \
  curl -X POST -d '{"text":"down"}' "$WEBHOOK"

# 디스크 사용 80% 넘으면 경보 (매시)
0 * * * * df -h / | awk 'NR==2 && +$5>80{print}' | \
  mail -s "[disk]" ops@example.com -e

# 매주 일요일 03:00 logrotate 강제
0 3 * * 0 /usr/sbin/logrotate -f /etc/logrotate.conf

# nginx access 로그 매일 압축 (logrotate 미사용 시)
30 0 * * * gzip /var/log/nginx/access.log.$(date -d 'yesterday' +\%F)

# 시스템 패키지 보안 업데이트 새벽 2시
0 2 * * * apt-get update && apt-get -y -o Dpkg::Options::=--force-confold install -t \
  $(lsb_release -cs)-security
```

## 25.13 디버깅

```bash
# 실행 됐는지
sudo journalctl -t CRON --since today
sudo grep CRON /var/log/syslog | tail

# 환경 차이 재현
env -i HOME="$HOME" PATH=/usr/bin:/bin /bin/sh -c 'echo $PATH; ls'

# crontab 문법 검증
crontab -l | grep -v '^\s*#' | grep -v '^\s*$'

# 즉시 한 번 실행 (디버깅)
sudo run-parts --verbose /etc/cron.daily
```

다음 챕터: [제26장]

\newpage

---


# 26. screen 과 tmux — 분리 가능한 세션

> SSH가 끊겨도 작업이 살아남는다. 한 단말에 여러 화면.

## 26.1 왜 필요한가

```
원격 서버에 ssh →  long-running 명령 →  네트워크 끊김 →  명령 죽음 ㅠ
```

screen / tmux 안에서 돌리면 SSH 끊겨도 명령은 계속. 다음 접속 시 `attach` 하면 다시 보임.

| 도구 | 특징 |
|------|------|
| screen | 거의 모든 시스템에 깔림. 단축키 단순 |
| tmux  | 더 현대적. 페이널, 상태바, 스크립팅 강함 |

새로 익힌다면 **tmux 권장**. 그래도 screen 만 깔린 서버는 흔하다.

## 26.2 tmux 빠른 시작

```bash
sudo apt install tmux
tmux                       # 새 세션 시작
tmux new -s work           # 이름 붙여 시작
tmux ls                    # 세션 목록
tmux attach                # 마지막에 attach
tmux attach -t work        # 이름으로
tmux a                     # 줄임
tmux kill-session -t work
tmux kill-server           # 모두 끝
```

기본 prefix: `Ctrl+b`. 모든 단축키는 prefix 누른 다음 키 입력.

### 자주 쓰는 키 (prefix Ctrl+b)

| 키 | 동작 |
|----|------|
| `?` | 도움말 |
| `d` | detach (세션 살아있음) |
| `c` | 새 윈도 |
| `,` | 윈도 이름 |
| `n` / `p` | 다음/이전 윈도 |
| `0`~`9` | 번호로 점프 |
| `w` | 윈도 목록 |
| `&` | 윈도 종료 |
| `"` | 가로 분할 |
| `%` | 세로 분할 |
| `o` | 다음 페인 |
| 화살표 | 페인 이동 |
| `q` | 페인 번호 잠깐 표시 |
| `z` | 페인 줌 토글 |
| `x` | 페인 종료 |
| `{` `}` | 페인 위치 교환 |
| `Space` | 레이아웃 순환 |
| `[` | 복사 모드 (스크롤백) |
| `]` | 붙여넣기 |
| `:` | 명령 모드 |
| `t` | 시계 |
| `s` | 세션 목록 |

### 흐름 예제

```bash
ssh user@host
tmux new -s deploy
# 안에서
./long-deploy.sh
# Ctrl+b d → detach
exit                  # SSH 종료
# 다음 날
ssh user@host
tmux a -t deploy      # 작업 그대로
```

### 페인 분할 + 레이아웃

```
Ctrl+b "    가로 분할
Ctrl+b %    세로 분할
Ctrl+b z    줌 토글
Ctrl+b 화살표  이동
Ctrl+b Space  레이아웃 순환
```

레이아웃 이름:
- even-horizontal, even-vertical
- main-horizontal, main-vertical
- tiled

```
Ctrl+b : select-layout tiled
```

### 스크롤백 / 복사

```
Ctrl+b [
# 화살표/PageUp 으로 스크롤
# Space = 선택 시작 (vi 모드)
# Enter = 복사
# Ctrl+b ] = 붙여넣기
```

vi 모드 권장 (`set -g mode-keys vi`).

### 마우스

```
Ctrl+b : set -g mouse on
```

마우스 휠로 스크롤, 클릭으로 페인 선택, 드래그로 크기 조정.

## 26.3 ~/.tmux.conf 추천 시작점

```tmux
# 더 편한 prefix
unbind C-b
set -g prefix C-a
bind C-a send-prefix

# 색
set -g default-terminal "screen-256color"
set -ga terminal-overrides ",xterm-256color:Tc"

# 마우스
set -g mouse on

# 인덱스 1부터
set -g base-index 1
setw -g pane-base-index 1
set -g renumber-windows on

# 빠른 escape (vim 친화)
set -sg escape-time 10

# 히스토리
set -g history-limit 100000

# 분할 키 직관적으로
bind | split-window -h -c "#{pane_current_path}"
bind - split-window -v -c "#{pane_current_path}"
unbind '"'
unbind %

# 빠른 reload
bind r source-file ~/.tmux.conf \; display "Reloaded!"

# vi 키 (복사 모드)
setw -g mode-keys vi
bind -T copy-mode-vi v send -X begin-selection
bind -T copy-mode-vi y send -X copy-pipe-and-cancel "xclip -selection clipboard"

# 상태바
set -g status-interval 5
set -g status-left "[#S] "
set -g status-right "%Y-%m-%d %H:%M  #(whoami)@#H"
set -g status-style "bg=black,fg=white"
```

`Ctrl+a r` 로 재로드.

## 26.4 tmux 명령 모드 / 스크립팅

`Ctrl+b :` 로 명령 모드:

```
new-window -n logs
split-window -v
send-keys -t 0 'tail -F /var/log/nginx/access.log' C-m
```

bash 에서 직접도 가능 (자동화):

```bash
tmux new-session -d -s monitor
tmux send-keys -t monitor 'htop' C-m
tmux split-window -v -t monitor
tmux send-keys -t monitor 'tail -F /var/log/syslog' C-m
tmux split-window -h -t monitor
tmux send-keys -t monitor 'watch -n 5 df -h' C-m
tmux attach -t monitor
```

대시보드 스크립트로 만들어 두면 매번 한 번에 띄울 수 있다.

## 26.5 screen 빠른 시작

```bash
sudo apt install screen
screen                     # 새 세션
screen -S work             # 이름
screen -ls                 # 목록
screen -r work             # attach
screen -d -r work          # 다른 데서 붙어 있으면 떼고 가져오기
screen -x work             # 공유 attach
screen -X -S work quit     # 종료
```

기본 prefix: `Ctrl+a`.

### 자주 쓰는 단축키

| 키 | 동작 |
|----|------|
| `Ctrl+a c` | 새 윈도 |
| `Ctrl+a n` `p` | 다음/이전 |
| `Ctrl+a 0..9` | 번호 점프 |
| `Ctrl+a "` | 윈도 목록 |
| `Ctrl+a A` | 이름 변경 |
| `Ctrl+a d` | detach |
| `Ctrl+a S` | 가로 분할 (region) |
| `Ctrl+a |` | 세로 분할 |
| `Ctrl+a Tab` | region 이동 |
| `Ctrl+a X` | region 닫기 |
| `Ctrl+a Q` | 다른 region 닫기 (only) |
| `Ctrl+a [` | 복사 모드 (스크롤) |
| `Ctrl+a ]` | 붙여넣기 |
| `Ctrl+a :` | 명령 |
| `Ctrl+a ?` | 도움말 |

### ~/.screenrc 추천

```
defscrollback 100000
startup_message off
hardstatus on
hardstatus alwayslastline "%{= kw}%-w%{=br kw}%n %t%{-}%+w %=%C %d/%m"
shell -$SHELL
defutf8 on
altscreen on
```

## 26.6 tmux 와 screen 비교

| 항목 | screen | tmux |
|------|--------|------|
| prefix | Ctrl+a | Ctrl+b (자주 Ctrl+a 로 변경) |
| 페인 분할 | 됨 (region) | 강력 |
| 명령 스크립팅 | 약함 | 매우 강함 |
| 클라이언트 다중 attach | OK | OK |
| 상태바 | 약함 | 풍부 |
| copy mode | 약간 어색 | vi 모드 친화 |
| 마우스 | 없음 | 풍부 |
| 의존성 | 어디나 깔림 | 추가 설치 필요할 때 있음 |

새 시스템 → tmux. 익숙한 환경 / 어디나 → screen.

## 26.7 byobu — 친절한 wrapper

```bash
sudo apt install byobu
byobu                # tmux/screen 위에서 깔끔한 상태바, 키 도움말
byobu-enable         # 로그인 시 자동
```

처음 익히기 좋다.

## 26.8 zellij — 현대적 대안 (보너스)

Rust 로 쓰여진 새로운 멀티플렉서. 단축키가 화면에 항상 표시되어 학습 부담 적음.

```bash
sudo apt install zellij     # 또는 cargo install
zellij
```

이 책 범위 외이지만 추천.

## 26.9 자주 쓰는 패턴

### 원격 빌드/배포 — 안전하게

```bash
ssh host
tmux new -s build
make -j8 deploy
# Ctrl+b d
exit
# 끊어져도 안전. 다음에 재접속:
ssh host
tmux a -t build
```

### 다중 호스트 모니터

```bash
tmux new -s mon
# Ctrl+b "
ssh web1 'top -b'
# Ctrl+b "
ssh web2 'top -b'
```

### 동기화 입력 (모든 페인 동시)

```
tmux: Ctrl+b : setw synchronize-panes on
screen: Ctrl+a :  설정/명령 미지원 (cssh 등 외부 도구)
```

`cssh` 또는 `clusterssh` 가 더 적합한 도구.

### 배포 모니터 + 로그 + DB

```bash
tmux new -s ops
# Window 1: htop
# Window 2:
#   pane left: tail -F nginx/access.log
#   pane right: tail -F nginx/error.log
# Window 3: psql production
```

스크립트로 자동 생성:

```bash
#!/bin/bash
S=ops
tmux new-session -d -s "$S" -n top
tmux send-keys -t "$S:top" 'htop' C-m

tmux new-window -t "$S" -n logs
tmux send-keys -t "$S:logs" 'sudo tail -F /var/log/nginx/access.log' C-m
tmux split-window -h -t "$S:logs"
tmux send-keys -t "$S:logs" 'sudo tail -F /var/log/nginx/error.log' C-m

tmux new-window -t "$S" -n db
tmux send-keys -t "$S:db" 'psql production' C-m

tmux attach -t "$S"
```

## 26.10 함정과 팁

| 함정 | 대처 |
|------|------|
| Ctrl+S 가 단말 멈춤 | `stty -ixon` 로 흐름 제어 끔 |
| escape 가 느림 | tmux: `set -sg escape-time 10` |
| 한글 깨짐 | `LANG=C.UTF-8`, `set -g default-terminal "tmux-256color"` |
| 부모 셸 환경 안 따라옴 | `default-shell`, `default-command` 명시 |
| 색이 안 살아남 | `terminal-overrides ",*256col*:Tc"` |
| copy-mode 가 어색 | vi 모드 활성화 |
| 자동 detach | `set -g detach-on-destroy off` |

다음 챕터: [제27장]

\newpage

---


# 27. nohup, jobs, fg, bg, disown, &

> 단말 끊김에도 살아남는 백그라운드 실행, 잡 컨트롤.

## 27.1 잡(job) 개념

셸이 실행시킨 자식 프로세스의 그룹.

- **포어그라운드**: 현재 단말을 점유 (입력/Ctrl+C 받음)
- **백그라운드**: 단말 안 점유, 출력은 그대로 흐름
- **stopped**: SIGTSTP/Ctrl+Z 로 정지된 상태

`%N` 으로 잡 참조.

```bash
sleep 1000 &        # 백그라운드
[1] 1234

jobs
[1]+  Running   sleep 1000 &

fg %1               # 포어그라운드로
# Ctrl+Z → 정지
[1]+  Stopped     sleep 1000

bg %1               # 다시 백그라운드
fg                  # 마지막 잡

kill %1             # 종료
```

| 표기 | 의미 |
|------|------|
| `%1` | 잡 1 |
| `%+` 또는 `%%` | 현재 잡 |
| `%-` | 직전 잡 |
| `%문자열` | 명령으로 시작하는 잡 |
| `%?문자열` | 명령에 포함하는 잡 |

## 27.2 jobs

```bash
jobs                # 잡 목록
jobs -l             # PID 포함
jobs -p             # PID 만
jobs -r             # running 만
jobs -s             # stopped 만
```

상태 표시:

| 표기 | 의미 |
|------|------|
| `Running` | 실행 중 |
| `Stopped` | 정지 |
| `Done` | 정상 종료 |
| `Exit N` | N 코드로 종료 |
| `Terminated` | 시그널로 |

## 27.3 & — 백그라운드 실행

```bash
long-task &
ls *.log | xargs gzip &
./build.sh > build.log 2>&1 &
```

출력을 안 잡으면 백그라운드여도 화면에 섞인다 → 항상 리다이렉트.

`$!` 는 직전 백그라운드 PID.

```bash
long-task &
PID=$!
sleep 60
kill $PID
```

## 27.4 nohup — 단말 끊김 무시

`nohup` 은 SIGHUP 을 무시하게 만들고, 표준입출력을 파일로 분리.

```bash
nohup ./run.sh &
# nohup.out 에 stdout/stderr

nohup ./run.sh > /var/log/run.log 2>&1 &

nohup long-task &
exit                # 단말 종료해도 long-task 살아있음
```

기본 출력 파일:
- `~/nohup.out` 또는 `./nohup.out` (쓰기 가능한 곳)

### 단말 닫고 떠나는 정석

```bash
nohup ./run.sh > /var/log/run.log 2>&1 < /dev/null &
disown
exit
```

- stdout/err 파일로
- stdin 을 `/dev/null` 로 (입력 대기 회피)
- `disown` 로 잡 테이블에서 제거

## 27.5 disown — 셸 잡 테이블에서 제거

이미 백그라운드로 돌고 있는 잡을 셸 종료해도 살아남게.

```bash
./run.sh &
disown                # 마지막 잡
disown %1             # 특정 잡
disown -h %1          # SIGHUP 만 막음 (잡 테이블 유지)
disown -a             # 모든 잡
```

`disown -h` 는 잡 목록에는 남지만 SIGHUP 은 안 받는다.

## 27.6 setsid — 새 세션 + 새 프로세스 그룹

부모 단말과 완전히 독립된 프로세스를 만든다.

```bash
setsid ./daemon.sh < /dev/null > /var/log/d.log 2>&1
# 부모(현재 셸)와 무관하게 동작
```

systemd 서비스 만들 만큼은 아니지만 단말과 분리하고 싶을 때.

```bash
setsid bash -c '
  trap "" HUP
  exec ./run.sh > /var/log/run.log 2>&1 < /dev/null
'
```

## 27.7 잡 컨트롤 단축키

| 키 | 동작 |
|----|------|
| `Ctrl+Z` | 포어그라운드 잡 정지 (SIGTSTP) |
| `Ctrl+C` | 인터럽트 (SIGINT) |
| `Ctrl+\ ` | 코어덤프 + 종료 (SIGQUIT) |
| `Ctrl+D` | EOF (입력 끝) |

정지 후 `bg` 로 백그라운드 진행 가능 → "이 작업 시간 걸리니까 일단 셸로 돌아가자" 패턴.

```bash
# 큰 grep 시작
big-search

# 너무 오래 걸림 → Ctrl+Z
^Z
[1]+  Stopped   big-search

bg
[1]+ big-search &

# 다른 작업 진행하면서
ls
ps
```

## 27.8 wait — 백그라운드 종료 대기

```bash
./a.sh &
A=$!
./b.sh &
B=$!

wait $A $B
echo "둘 다 끝났음"

# 종료 코드 확인
wait $A; echo "A: $?"
wait $B; echo "B: $?"
```

```bash
# 모든 백그라운드 잡 기다림
wait
```

`wait -n` (bash 4.3+): 첫 번째 끝나는 잡만 대기.

## 27.9 trap 으로 정리

```bash
#!/bin/bash
PID=
cleanup() { [ -n "$PID" ] && kill "$PID" 2>/dev/null; }
trap cleanup EXIT

long-task &
PID=$!

sleep 30        # 일부 시간 기다림
echo "done"
# trap 이 자식 정리
```

자식 그룹 통째로 정리:

```bash
trap 'kill -- -$$' EXIT
# $$ 은 현재 셸 PID = 프로세스 그룹 ID
```

## 27.10 흔한 패턴 / 한 줄

```bash
# 단말 끊김에도 살아남는 작업
nohup ./run.sh > out.log 2>&1 < /dev/null &
disown

# 여러 작업 병렬 + 모두 끝나면 진행
for i in 1 2 3 4; do
  ./worker.sh "$i" > "log.$i" 2>&1 &
done
wait
echo "all done"

# 첫 번째 끝나면 종료 (race)
{ slow_thing; echo SLOW; } &
{ fast_thing; echo FAST; } &
wait -n
kill 0     # 같은 프로세스 그룹 다 종료

# 진행 표시 (로딩 spinner)
spin() {
  local pid=$1
  local s='|/-\'
  while kill -0 "$pid" 2>/dev/null; do
    for c in / - \\ \|; do
      printf '\r[%c] working' "$c"; sleep 0.1
    done
  done
  printf '\r[done]    \n'
}

long-task & spin $!

# 백그라운드 출력 별도 파일 분리
{ ./long.sh > /tmp/long.out 2> /tmp/long.err & }
disown
```

## 27.11 systemd-run 으로 즉석 데몬화

`nohup` / `disown` 보다 깔끔. 자세한 건 [제23장].

```bash
systemd-run --user --unit=mybg --remain-after-exit \
  /usr/local/bin/long-task.sh

systemctl --user status mybg
journalctl --user -u mybg -f
systemctl --user stop mybg
```

## 27.12 흔한 함정

| 함정 | 대처 |
|------|------|
| stdin 안 닫아 → 입력 대기로 hang | `< /dev/null` |
| 출력 안 잡아 → 화면 섞임 | `> file 2>&1` |
| `nohup`만 하고 disown 안 함 | 셸 종료 시 잡 정리 (배포판마다 다름) |
| `nohup`이 출력 못 쓸 곳에서 동작 | 명시적 `> /var/log/...` |
| 셸 종료해도 안 죽는 게 좋다 → 사실은 systemd 가 정답 | `systemd-run` |
| 부모 죽으면 자식도 → 잡이 SIGHUP | `nohup` 또는 `disown -h` |
| `kill %1` 인데 안 죽음 | 자식 그룹 - `kill -- -PGID` |

다음 챕터: [제28장]

\newpage

---


# 28. lsof — 열린 파일 추적

> 모든 것은 파일이다. 그래서 lsof 가 거의 모든 디버깅에 쓸모있다.

## 28.1 무엇을 보여주나

`lsof` = "list open files". 리눅스에서 파일은 디스크 파일뿐 아니라 소켓, 파이프, 디바이스, 디렉토리까지 모두 포함.

```bash
sudo apt install lsof
sudo lsof | head
```

권한 없으면 자기 프로세스만 보임. 시스템 전체 진단은 보통 sudo.

## 28.2 출력 컬럼

```
COMMAND    PID  USER   FD   TYPE DEVICE SIZE/OFF   NODE NAME
nginx    12345  www  4u    IPv4 12345  0t0       TCP  *:http (LISTEN)
```

| 컬럼 | 의미 |
|------|------|
| COMMAND | 명령 이름 |
| PID | 프로세스 ID |
| USER | 사용자 |
| FD | 파일 디스크립터 (cwd, txt, mem, 0~N) |
| TYPE | REG, DIR, IPv4, IPv6, unix, FIFO, CHR, BLK |
| DEVICE | 디바이스 |
| SIZE/OFF | 크기 또는 오프셋 |
| NODE | inode |
| NAME | 경로 / 주소 |

### FD 종류

| FD | 의미 |
|----|------|
| `cwd` | 현재 작업 디렉토리 |
| `rtd` | 루트 디렉토리 (chroot) |
| `txt` | 실행 파일 텍스트 (코드) |
| `mem` | 메모리 매핑 파일 |
| `mmap` | 메모리 매핑 |
| `DEL` | 삭제됐지만 열려 있음 |
| `0u`, `1w`, `2r` | 0=stdin, 1=stdout, 2=stderr (`u`=read/write, `r`=read, `w`=write) |
| 숫자 | 일반 fd |

## 28.3 자주 쓰는 필터

```bash
sudo lsof -p PID                # 특정 프로세스
sudo lsof -c nginx              # 명령 이름
sudo lsof -u alice              # 사용자
sudo lsof -u ^root              # 사용자 제외
sudo lsof /var/log/nginx/access.log    # 그 파일을 누가 열었나
sudo lsof +D /var/www           # 디렉토리 안 모든 파일
sudo lsof -nP -i :80            # 포트 80
sudo lsof -nP -iTCP -sTCP:LISTEN
sudo lsof -nP -iTCP@10.0.5.10
sudo lsof -i 4 -n               # IPv4 만
sudo lsof -i 6 -n               # IPv6
sudo lsof -i UDP                # UDP
sudo lsof +L1                   # 링크가 0 인 파일 (삭제됐는데 열려있음)
sudo lsof -X                    # 더 빠르게 (XML 검사 생략)
```

`-n` IP 안 풀고, `-P` 포트 이름 안 풀고. 자동화에 유용.

## 28.4 핵심 디버깅 시나리오

### "포트 점유 누가?"

```bash
sudo lsof -nP -iTCP:8080 -sTCP:LISTEN
# 또는
sudo ss -ltnp 'sport = :8080'
```

`ss` 가 더 빠르고 현대적이지만 lsof 는 더 풍부한 정보.

### "파일 삭제했는데 디스크 안 줄어"

파일이 삭제됐어도 누군가 열고 있으면 inode 가 안 풀린다.

```bash
sudo lsof +L1               # 링크 카운트 0 인 열린 파일
sudo lsof / | sed -n '/(deleted)/p'
```

해당 프로세스를 재시작 또는 fd 를 닫게 만들면 디스크 회수.

긴급 회수 (서비스 재시작 못 할 때):

```bash
# 해당 fd 를 /dev/null 로 redirect
PID=1234; FD=5
sudo gdb -p $PID
> p close($FD)        # 또는
> p dup2(open("/dev/null", 0), $FD)
```

위험. 보통은 서비스 재시작이 안전.

### "디렉토리 unmount 가 안 됨"

```bash
sudo lsof +D /mnt/usb
# 또는
sudo fuser -m /mnt/usb
```

`fuser` 가 더 가볍다.

```bash
sudo fuser -mv /mnt/usb       # 누가 쓰는지
sudo fuser -k /mnt/usb        # 그 사용자 프로세스에 SIGKILL (조심)
sudo fuser -k -TERM /mnt/usb  # 정중하게
```

### "한 프로세스가 어떤 파일을 열고 있나"

```bash
sudo lsof -p $(pidof nginx | awk '{print $1}')
sudo ls -l /proc/PID/fd/        # 같은 정보
```

### "어느 라이브러리가 로드됐나"

```bash
sudo lsof -p PID | sed -n '/mem/p'
cat /proc/PID/maps
```

## 28.5 네트워크 보기

```bash
# LISTEN 중인 모든 포트
sudo lsof -nP -iTCP -sTCP:LISTEN

# 특정 호스트 연결
sudo lsof -nP -i@10.0.5.10

# 특정 포트 연결
sudo lsof -nP -i :443

# ESTABLISHED 연결만
sudo lsof -nP -iTCP -sTCP:ESTABLISHED

# 한 프로세스의 네트워크
sudo lsof -nP -p PID -i

# 누가 외부와 연결?
sudo lsof -nP -iTCP -sTCP:ESTABLISHED | grep -v 127.0.0.1
```

## 28.6 -r 반복 모드

```bash
sudo lsof -nP -iTCP:443 -r 2          # 2초마다 갱신
sudo lsof -p PID +r 5                 # 변화 있을 때만 출력
```

## 28.7 -F 머신 친화 출력 (파싱)

```bash
sudo lsof -nP -iTCP:80 -F pcL
# p1234
# cnginx
# Lwww-data
# ...
```

각 토큰: p=PID, c=COMMAND, L=USER. 스크립트로 파싱하기 쉽다.

```bash
sudo lsof -t -i :80         # PID 만 (정수)
```

## 28.8 fuser — 더 가벼운 형제

```bash
fuser /var/log/nginx/access.log     # 누가 열었나
fuser -m /mnt/usb                    # 마운트 포인트 사용자
fuser -k -TERM /var/run/foo.sock     # 정중 종료
fuser -k -9 /var/run/foo.sock        # 강제

fuser -nv tcp 80                     # TCP:80 누가
fuser -n udp 53                      # UDP:53
```

## 28.9 ss / netstat 와 결합

[제30장]에서 자세히. lsof 가 비싼 작업이라 시작은 ss 로 좁혀라.

```bash
ss -ltnp 'sport = :443'         # 빠른 포트 점유 확인
sudo lsof -nP -p PID            # 그 PID 의 모든 fd 자세히
```

## 28.10 자주 쓰는 한 줄

```bash
# 디스크 100% 인데 du 와 df 가 안 맞음 → 삭제됐지만 열려 있음
sudo lsof +L1 | head

# 80, 443 점유 중인 프로세스
sudo lsof -nP -iTCP:80,443 -sTCP:LISTEN

# 어떤 프로세스가 /var/lib/postgresql 에 쓰고 있나
sudo lsof +D /var/lib/postgresql

# 가장 많은 fd 가진 프로세스 톱 5
for pid in $(ls /proc | grep -E '^[0-9]+$'); do
  c=$(ls /proc/$pid/fd 2>/dev/null | wc -l)
  echo "$c $pid"
done | sort -rn | head

# 한 프로세스의 listen / connect 만
sudo lsof -nPp PID -iTCP

# 사라진 파일을 통해 계속 쓰는 로그 (logrotate 후 신규 안 잡힘)
sudo lsof -nP -p $(pidof nginx) | sed -n '/log/Ip'
# → 새 파일 안 보면 nginx -s reopen 또는 USR1
```

## 28.11 함정

| 함정 | 대처 |
|------|------|
| 일반 사용자만 보임 | `sudo` |
| 매우 느림 (수만 fd) | `-X`, `-n -P` 로 가속, `+D` 자제 |
| 컨테이너 안 PID 와 호스트 PID 다름 | 호스트에서 `nsenter` 또는 컨테이너 안 lsof |
| FUSE 마운트 (sshfs) 의 fd | 호스트에서 보임, 표기 다름 |
| `+D` 가 실제로 디렉토리 안을 모두 검사 | 큰 트리에선 매우 느림 |

다음 챕터: [제29장]

\newpage

---


# 29. 네트워크 설정 — ip, ifconfig, route, nmcli

> 인터페이스, IP, 라우팅. ifconfig/route 는 구식, ip 가 현대 표준.

## 29.1 도구 지형도

| 도구 | 상태 |
|------|------|
| `ip` (iproute2) | **현대 표준** |
| `ifconfig` (net-tools) | 구식, 일부 정보 누락. 기본 없는 배포판 多 |
| `route` | 구식. `ip route` 로 대체 |
| `nmcli` | NetworkManager (Ubuntu/Fedora 데스크탑/서버) |
| `networkctl` | systemd-networkd |
| `iw` / `iwconfig` | 무선 |

`ip` + (필요시) `nmcli` 또는 `networkctl` 로 거의 모든 일을 한다.

## 29.2 ip addr — 인터페이스/주소

```bash
ip addr             # 또는 ip a
ip -br addr         # brief
ip -c addr          # 컬러
ip -4 addr          # IPv4 만
ip -6 addr          # IPv6
ip addr show eth0
```

```
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 ...
    inet 192.168.1.10/24 brd 192.168.1.255 scope global dynamic eth0
    inet6 fe80::1/64 scope link
```

### 인터페이스 활성/비활성

```bash
sudo ip link set eth0 up
sudo ip link set eth0 down

# 별칭/MAC 변경
sudo ip link set eth0 address 02:11:22:33:44:55

# MTU 변경
sudo ip link set eth0 mtu 9000
```

### IP 추가/삭제

```bash
sudo ip addr add 192.168.1.50/24 dev eth0
sudo ip addr add 10.0.0.5/24 dev eth0 label eth0:0    # alias
sudo ip addr del 192.168.1.50/24 dev eth0
sudo ip addr flush dev eth0
```

영구 설정은 배포판별 (netplan, NetworkManager, /etc/network/interfaces, systemd-networkd).

## 29.3 ip link — 인터페이스 자체

```bash
ip link             # 모든 인터페이스
ip -br link         # 한 줄씩 요약
ip link show eth0
ip link show type bridge
ip link show type vlan
```

상태:

| 표기 | 의미 |
|------|------|
| `UP` | 행정적 활성 |
| `LOWER_UP` | 물리적 링크 |
| `DOWN` | 비활성 |
| `NO-CARRIER` | 케이블 빠짐 |
| `PROMISC` | 프로미스큐어스 (모든 패킷 수신) |

### 가상 인터페이스

```bash
# bridge
sudo ip link add br0 type bridge
sudo ip link set eth0 master br0
sudo ip link set br0 up

# bond
sudo ip link add bond0 type bond mode 802.3ad
sudo ip link set eth0 master bond0
sudo ip link set eth1 master bond0

# vlan
sudo ip link add link eth0 name eth0.100 type vlan id 100

# veth (컨테이너용)
sudo ip link add veth0 type veth peer name veth1
```

## 29.4 ip route — 라우팅 테이블

```bash
ip route                    # 또는 ip r
ip -6 route
ip route show table all
ip route get 8.8.8.8        # 어느 경로로 갈까?
```

```
default via 192.168.1.1 dev eth0 proto dhcp src 192.168.1.10 metric 100
192.168.1.0/24 dev eth0 proto kernel scope link src 192.168.1.10
```

| 컬럼 | 의미 |
|------|------|
| `default` | 기본 게이트웨이 |
| `via` | 다음 홉 |
| `dev` | 출구 인터페이스 |
| `proto` | 추가 주체 (kernel, dhcp, static 등) |
| `scope` | link / global / host |
| `src` | 출발지 IP |
| `metric` | 우선순위 (낮은 게 먼저) |

### 라우트 추가/삭제

```bash
sudo ip route add 10.0.0.0/8 via 192.168.1.1
sudo ip route add 10.0.0.0/8 dev tun0
sudo ip route add default via 192.168.1.1
sudo ip route del 10.0.0.0/8
sudo ip route flush table main
```

여러 테이블 / 정책 라우팅:

```bash
sudo ip rule add from 10.0.0.0/8 table 100
sudo ip route add default via 10.0.0.1 table 100
ip rule
```

## 29.5 ip neigh — ARP 테이블

```bash
ip neigh                       # = ip n
ip neigh show dev eth0
sudo ip neigh add 192.168.1.5 lladdr 02:aa:bb:cc:dd:ee dev eth0
sudo ip neigh flush all
```

## 29.6 ifconfig — 구식이지만 흔히 만남

```bash
sudo apt install net-tools     # 없는 배포판이 흔함

ifconfig
ifconfig eth0
sudo ifconfig eth0 up
sudo ifconfig eth0 down
sudo ifconfig eth0 192.168.1.50 netmask 255.255.255.0
sudo ifconfig eth0 mtu 9000
sudo ifconfig eth0 hw ether 02:11:22:33:44:55
sudo ifconfig eth0 promisc       # 또는 -promisc
```

`ifconfig` 만의 정보:
- TX/RX 패킷 카운터, 충돌 수 (ip 는 `ip -s link` 로)

```bash
ip -s link show eth0      # 통계
```

새 시스템은 `ip` 사용. 옛 스크립트 / 임베디드 빼고 `ifconfig` 외울 필요 없음.

## 29.7 route 명령

```bash
sudo apt install net-tools
route -n           # 숫자
route -nee
sudo route add default gw 192.168.1.1
sudo route add -net 10.0.0.0/8 gw 192.168.1.1
sudo route del -net 10.0.0.0/8
```

대체:

```bash
ip route
ip route get 1.2.3.4
```

## 29.8 영구 설정 — 배포판별

### Debian/Ubuntu — netplan (현대)

`/etc/netplan/01-net.yaml`:

```yaml
network:
  version: 2
  renderer: networkd
  ethernets:
    eth0:
      addresses:
        - 192.168.1.10/24
      gateway4: 192.168.1.1
      nameservers:
        addresses: [1.1.1.1, 8.8.8.8]
      mtu: 1500
```

```bash
sudo netplan try        # 시뮬레이션 (롤백 가능)
sudo netplan apply
```

### Debian — /etc/network/interfaces (구식이지만 많이 보임)

```
auto eth0
iface eth0 inet static
    address 192.168.1.10
    netmask 255.255.255.0
    gateway 192.168.1.1
    dns-nameservers 1.1.1.1 8.8.8.8

iface eth0 inet dhcp
```

```bash
sudo ifup eth0
sudo ifdown eth0
```

### NetworkManager — nmcli

```bash
nmcli                       # 현재 상태
nmcli device
nmcli connection             # = nmcli con
nmcli con show
nmcli con show "Wired connection 1"

# 새 정적 연결
sudo nmcli con add type ethernet con-name "static-eth" ifname eth0 \
  ip4 192.168.1.10/24 gw4 192.168.1.1
sudo nmcli con mod static-eth ipv4.dns "1.1.1.1 8.8.8.8" ipv4.method manual
sudo nmcli con up static-eth

# Wi-Fi
nmcli dev wifi list
sudo nmcli dev wifi connect "MyAP" password "secret"

# 활성 연결 끊기/켜기
sudo nmcli con down myname
sudo nmcli con up myname
```

### systemd-networkd

`/etc/systemd/network/10-eth0.network`:

```
[Match]
Name=eth0

[Network]
Address=192.168.1.10/24
Gateway=192.168.1.1
DNS=1.1.1.1
```

```bash
sudo systemctl restart systemd-networkd
networkctl
networkctl status eth0
```

### RHEL/Fedora 구식 — /etc/sysconfig/network-scripts/

```
DEVICE=eth0
BOOTPROTO=static
ONBOOT=yes
IPADDR=192.168.1.10
NETMASK=255.255.255.0
GATEWAY=192.168.1.1
DNS1=1.1.1.1
```

새 RHEL 9+ 는 NetworkManager keyfile (`/etc/NetworkManager/system-connections/*.nmconnection`) 사용.

## 29.9 DNS 설정

`/etc/resolv.conf` (직접 편집은 시스템에 따라 덮어씌워짐):

```
nameserver 1.1.1.1
nameserver 8.8.8.8
search example.com
options timeout:2 attempts:1
```

systemd-resolved:

```bash
resolvectl status
resolvectl dns eth0 1.1.1.1 8.8.8.8
sudo systemctl restart systemd-resolved
```

NetworkManager:

```bash
nmcli con mod "myname" ipv4.dns "1.1.1.1 8.8.8.8"
sudo nmcli con up "myname"
```

## 29.10 호스트 이름

```bash
hostname              # 현재
sudo hostname newname # 임시
hostnamectl           # systemd 상세
sudo hostnamectl set-hostname newname
```

`/etc/hostname`, `/etc/hosts` 도 일치시킨다.

## 29.11 통계 / 진단

```bash
# 인터페이스 통계
ip -s link show eth0
ip -s -s link show eth0       # 더 자세히

# 패킷 흐름 실시간
ifstat              # 또는 sudo apt install ifstat
nload eth0
bmon
iftop -i eth0
nethogs eth0        # 프로세스별

# 라우트 추적
mtr 8.8.8.8
traceroute 8.8.8.8
ip route get 8.8.8.8

# 도달성
ping -c 4 8.8.8.8
ping6 -c 4 ::1
```

자세한 진단은 [제31장], [제32장].

## 29.12 Termux / 안드로이드

- `ifconfig`, `ip` 일부 동작 (root 아니면 보기만)
- 모바일 데이터/Wi-Fi 정보:
  ```bash
  termux-wifi-connectioninfo
  termux-wifi-scaninfo
  ```
  (api 패키지 필요)

## 29.13 자주 쓰는 한 줄

```bash
# 내 IP 빠르게
ip -4 -br addr | awk '{print $1, $3}'
# 또는 외부에서 본 IP
curl -4 ifconfig.me

# 기본 게이트웨이
ip route | awk '/^default/{print $3}'

# 인터페이스 다 비활성/활성
for i in eth0 eth1; do sudo ip link set "$i" down; done
for i in eth0 eth1; do sudo ip link set "$i" up; done

# 추가 IP (alias) 임시
sudo ip addr add 192.168.1.99/24 dev eth0

# 임시 라우트
sudo ip route add 10.0.0.0/8 via 192.168.1.254 metric 50

# DNS 응답 확인
resolvectl query example.com
dig example.com

# arping 으로 IP 충돌 검사
sudo arping -c 3 -D -I eth0 192.168.1.50
```

다음 챕터: [제30장]

\newpage

---


# 30. ss 와 netstat — 소켓 통계

> 어떤 포트가 열렸나? 어떤 연결이 오갔나? ss 가 현대, netstat 은 구식이지만 흔함.

## 30.1 도구 비교

| 도구 | 상태 |
|------|------|
| `ss` (iproute2) | 현대 표준. 빠르고 풍부 |
| `netstat` (net-tools) | 구식. 깔리지 않은 시스템 多 |
| `lsof -i` | 프로세스 정보가 풍부 (느림) |
| `nmap` | 외부에서 본 포트 |

## 30.2 ss 기본

```bash
ss                    # 모든 비-listen 연결
ss -t                 # TCP
ss -u                 # UDP
ss -x                 # Unix 도메인
ss -l                 # listening
ss -a                 # 모두
ss -n                 # 숫자 (DNS 안 풂)
ss -p                 # 프로세스 (root 권장)
ss -e                 # 자세히
ss -o                 # 타이머
ss -m                 # 메모리
ss -s                 # 요약 통계
```

자주 쓰는 조합:

```bash
sudo ss -tlnp                # TCP listen + PID
sudo ss -tunap               # 모든 TCP/UDP + PID
ss -tn state established     # 확립된 TCP
ss -tn state time-wait       # TIME_WAIT
ss -tn state close-wait      # CLOSE_WAIT (문제 신호)
ss -tn '( sport = :22 or dport = :22 )'
ss -tn 'dst 1.2.3.4'
ss -tn 'src 192.168.1.10'
ss -tn '( sport = :80 or sport = :443 )' state established
```

### 컬럼 의미

```
State    Recv-Q  Send-Q  Local Address:Port   Peer Address:Port  Process
LISTEN   0       128     0.0.0.0:80           0.0.0.0:*          users:(("nginx",pid=1234,fd=4))
ESTAB    0       0       10.0.0.5:443         1.2.3.4:50000
TIME-WAIT 0      0       10.0.0.5:443         1.2.3.4:60000
```

| 항목 | 의미 |
|------|------|
| State | TCP 상태 |
| Recv-Q | 수신 큐 (LISTEN 에선 큐 깊이) |
| Send-Q | 송신 큐 (LISTEN 에선 backlog 한계) |
| Local | 로컬 주소:포트 |
| Peer | 상대 주소:포트 |
| Process | 사용자/PID/FD (sudo 필요) |

### TCP 상태 빠른 사전

| 상태 | 의미 |
|------|------|
| LISTEN | 연결 대기 |
| SYN-SENT | 클라이언트 SYN 보냄 |
| SYN-RECV | 서버 SYN 받음 |
| ESTAB | 정상 연결 |
| FIN-WAIT-1/2 | 종료 진행 |
| TIME-WAIT | 종료 후 대기 (보통 60초) |
| CLOSE-WAIT | 상대가 끊었는데 우리가 close 안 함 → **버그 의심** |
| LAST-ACK | |
| CLOSING | 동시 종료 |
| CLOSED | |

`CLOSE-WAIT` 가 쌓이면 애플리케이션이 fd 를 안 닫는 것. 진단해야 함.

## 30.3 자주 쓰는 ss 한 줄

```bash
# 누가 80, 443 LISTEN?
sudo ss -tlnp 'sport = :80 or sport = :443'

# ESTABLISHED 연결 IP 별 카운트
ss -tn state established '( sport = :443 )' \
  | awk 'NR>1{split($5,a,":");print a[1]}' \
  | sort | uniq -c | sort -rn | head

# CLOSE-WAIT (애플 버그?)
sudo ss -tnp state close-wait

# TIME-WAIT 너무 많은가
ss -tn state time-wait | wc -l

# UDP listen
sudo ss -ulnp

# Unix 도메인
sudo ss -xa

# 타이머 / 재전송
ss -tno

# 메모리
ss -tm

# 다이얼로그 처음 backlog
ss -ltn
# State Recv-Q Send-Q  Local Address:Port
# LISTEN 0      128    0.0.0.0:80           ← Send-Q = backlog 한계
```

## 30.4 ss 필터 문법

```
sport = :22         # local port
dport = :443        # remote port
src 10.0.0.0/8      # local addr
dst 1.2.3.4/32      # remote addr
state STATE
```

논리 연산:

```bash
ss -tn '( sport = :443 or sport = :80 ) and dst 10.0.0.0/8'
ss -tn 'not ( sport = :22 )'
```

## 30.5 ss 통계

```bash
ss -s
# Total: 234
# TCP:   123 (estab 50, closed 60, orphaned 0, ...)
# Transport Total IP IPv6
# RAW       0     0  0
# UDP       12    8  4
# TCP       123   100 23
```

빠른 카운팅으로 비정상 감지.

## 30.6 netstat — 구식

깔려 있다면 그대로 쓰는 사람 많다. 핵심 옵션:

```bash
sudo netstat -tulnp        # TCP/UDP listen + PID
sudo netstat -an           # 모든 연결 (숫자)
sudo netstat -i            # 인터페이스 통계
sudo netstat -r            # 라우팅 (= ip route)
sudo netstat -s            # 프로토콜 통계
sudo netstat -c            # 1초 갱신
sudo netstat -gn           # 멀티캐스트 그룹
```

| 옵션 | 의미 |
|------|------|
| `-t` | TCP |
| `-u` | UDP |
| `-x` | Unix |
| `-l` | listening |
| `-a` | 모두 |
| `-n` | 숫자 |
| `-p` | 프로세스 (root) |
| `-r` | 라우팅 |
| `-i` | 인터페이스 |
| `-s` | 프로토콜별 통계 |
| `-c` | 갱신 |

`netstat -tulnp` ↔ `ss -tulnp`. 거의 1:1 대체.

## 30.7 ss 와 lsof 조합

```bash
# 빠른 리스닝 확인
sudo ss -ltnp 'sport = :3306'

# 프로세스 정보 더 깊게
sudo lsof -nP -p PID
```

## 30.8 자주 쓰는 진단 시나리오

### "왜 연결이 거절되나?"

```bash
# 1. listen 인가
sudo ss -lntp 'sport = :PORT'

# 2. 방화벽
sudo iptables -L INPUT -n -v --line-numbers
sudo nft list ruleset

# 3. 외부에서 도달
nc -zv host PORT
```

### "포트는 이미 사용 중"

```bash
sudo ss -lntp 'sport = :8080'
# nginx, pid=1234

# 옛 프로세스가 잡고 있다면
sudo systemctl restart nginx
# 또는
sudo kill 1234
```

### "TIME-WAIT 폭증"

짧은 연결을 계속 새로 만드는 클라이언트 때문. 보통은 정상이지만 한계 도달 시:

```bash
ss -tn state time-wait | wc -l
sysctl net.ipv4.tcp_tw_reuse
```

### "연결은 됐는데 데이터가 안 흐른다"

```bash
ss -tnio                    # 큐 + 타이머 보기
# Recv-Q 가 큰 채 멈춤 = 애플리케이션 read 안 함
# Send-Q 가 큰 채 멈춤 = 상대 ack 안 옴
ss -tnm                     # 메모리 사용량
```

### "방화벽 / NAT 환경에서 끊김"

```bash
ss -tno                     # 타이머 (keepalive 등)
```

`ServerAliveInterval` (SSH 측) 또는 `tcp_keepalive_time` 등.

## 30.9 sysctl 관련 튜닝 (참고)

```bash
sysctl net.ipv4.tcp_max_syn_backlog
sysctl net.core.somaxconn
sysctl net.ipv4.ip_local_port_range
sysctl net.ipv4.tcp_fin_timeout
sysctl net.ipv4.tcp_tw_reuse
```

문제 진단의 한 부분. 자세한 튜닝은 별도.

## 30.10 자주 쓰는 한 줄 모음

```bash
# 모든 listen 한 번에
sudo ss -tulnp

# 외부에서 본 listen (자기 IP 만)
sudo ss -tnlp '! src 127.0.0.1/8 and ! src ::1/128'

# IP 별 연결 수
ss -tn state established | awk 'NR>1{split($5,a,":");print a[1]}' \
  | sort | uniq -c | sort -rn | head

# 한 호스트가 우리 서버에 몇 개 연결
ss -tn dst 1.2.3.4 | wc -l

# 80, 443 외 listen 모두
sudo ss -tlnp '! ( sport = :80 or sport = :443 )'

# 도달성 빠른 확인
nc -zvw 3 host 443

# 어느 프로세스가 외부와 통신
sudo ss -tnp state established | sed -n '/users/p' | sort -k1,1 -u
```

다음 챕터: [제31장]

\newpage

---


# 31. ping, traceroute, mtr — 도달성 진단

> "거기 살아 있나?" 부터 "어디서 막히나?" 까지.

## 31.1 ping — 가장 단순한 도달성

```bash
ping host
ping -c 4 host             # 4번만
ping -i 0.5 host           # 0.5초 간격
ping -W 2 host             # 응답 대기 2초
ping -s 1400 host          # 패킷 크기
ping -M do -s 1472 host    # DF 비트 + 1472바이트 → MTU 진단
ping -f host               # flood (root, 조심)
ping -A host               # adaptive (응답 받으면 즉시 다음)
ping -q host               # 요약만
ping -t TTL host           # TTL 지정
ping -I eth0 host          # 인터페이스
ping -c 4 -W 2 -q 1.1.1.1  # 빠른 헬스체크
```

IPv4/v6:

```bash
ping -4 host
ping -6 host
ping6 host                 # 별도 명령 (구식)
ping ipv6.google.com
```

### 출력

```
PING google.com (142.250.207.78) 56(84) bytes of data.
64 bytes from xxx: icmp_seq=1 ttl=117 time=12.3 ms
...
--- google.com ping statistics ---
4 packets transmitted, 4 received, 0% packet loss, time 3005ms
rtt min/avg/max/mdev = 12.012/12.345/12.789/0.234 ms
```

| 항목 | 의미 |
|------|------|
| icmp_seq | 패킷 번호 |
| ttl | Time To Live (남은 홉) |
| time | RTT |
| packet loss | 손실률 |
| rtt | 최소/평균/최대/표준편차 |

손실 0% 라도 latency 폭증이 있으면 정체 신호.

### MTU / 단편화 진단

```bash
ping -M do -s 1472 host
# 1472 + 28(헤더) = 1500 = 표준 MTU
# 더 큰 값에서 'Frag needed' 나오면 그게 경로 MTU
```

## 31.2 ICMP 차단 환경

많은 클라우드/방화벽이 ICMP 를 막는다. 그땐 TCP ping:

```bash
# nc 로 포트 핑
nc -zvw 2 host 443

# nmap ping
nmap -sn host

# tcping (별도 설치)
sudo apt install hping3
hping3 -S -p 443 -c 4 host

# psping 류 — paping
```

## 31.3 traceroute — 경로 추적

```bash
traceroute host
traceroute -n host             # 숫자
traceroute -I host             # ICMP 모드
traceroute -T -p 443 host      # TCP SYN
traceroute -U host             # UDP (기본 다른 포트)
traceroute -q 1 host           # 홉당 프로브 1번 (빠름)
traceroute -m 20 host          # 최대 홉
```

```
1  192.168.1.1   1.2 ms  1.0 ms  0.9 ms
2  10.0.0.1      5.0 ms  5.2 ms  4.8 ms
3  *  *  *
4  1.1.1.1      12.0 ms  12.5 ms  11.9 ms
```

`* * *` 는 그 홉이 ICMP TTL exceeded 응답을 안 함 (방화벽). 트래픽이 통과는 가능할 수 있다.

### tracepath — 권한 없이

```bash
tracepath host
tracepath6 host
```

MTU 도 같이 보고.

## 31.4 mtr — ping + traceroute 합본

가장 강력한 진단 도구.

```bash
sudo apt install mtr
mtr host
mtr -n host             # 숫자
mtr -r -c 100 host      # 보고서 모드, 100번 측정
mtr -T -P 443 host      # TCP SYN to 443
mtr -u host             # UDP
mtr --json host
mtr --report --report-cycles 50 host > report.txt
```

연속 갱신 화면에서 어느 홉에서 손실률이 튀는지 즉시 보임.

| 컬럼 | 의미 |
|------|------|
| Loss% | 패킷 손실 |
| Snt | 보낸 수 |
| Last | 마지막 RTT |
| Avg | 평균 |
| Best | 최저 |
| Wrst | 최고 |
| StDev | 표준편차 |

손실은 마지막 홉만 보면 안 된다 (중간 ICMP rate-limit). **목적지 손실** 만 의미 있는 경우가 많다.

## 31.5 hping3 — 더 깊은 진단

```bash
sudo apt install hping3

# TCP SYN ping
sudo hping3 -S -p 443 -c 4 host

# ICMP timestamp
sudo hping3 --icmp --icmp-ts -c 3 host

# 특정 플래그
sudo hping3 -F -p 80 host         # FIN
sudo hping3 -A -p 80 host         # ACK

# 패킷 사이즈
sudo hping3 -S -p 443 -d 1400 host
```

DDoS 도구로 오해받기 쉬운데, 진단 목적으론 합법적이고 강력.

## 31.6 fping — 다중 호스트

```bash
sudo apt install fping
fping host1 host2 host3
fping -a -g 192.168.1.0/24      # alive 만 출력
fping -c 5 -q host
```

## 31.7 arping — L2 도달성

```bash
sudo apt install arping
sudo arping -c 3 -I eth0 192.168.1.1

# IP 충돌 검사 (DAD)
sudo arping -D -I eth0 -c 3 192.168.1.50
```

LAN 내부 디바이스 살아있나 확인 (라우터/L3 안 거침).

## 31.8 도달성 진단 흐름

```
ping host      → 응답 X
   ↓
ping gateway   → 응답 X → LAN 문제 (케이블, 인터페이스)
                  ↓ OK
ping 8.8.8.8   → 응답 X → ISP 라우터
                  ↓ OK
ping host      → 응답 X
ping ip(host)  → 응답 X → 호스트 문제
                  ↓ ip 응답 OK, 이름 X → DNS 문제
mtr host       → 어느 홉에서 멈추는지
nc -zv host port → 포트 차단?
```

## 31.9 자주 쓰는 한 줄

```bash
# 빠른 헬스체크 (스크립트용)
ping -c 1 -W 2 -q host >/dev/null && echo OK

# 손실률만
ping -c 100 -i 0.2 -q host | sed -n 's/.*\([0-9.]*\)% packet loss.*/\1/p'

# RTT 평균만
ping -c 10 -q host | sed -n 's|.*= [^/]*/\([^/]*\)/.*|\1|p'

# 모든 LAN alive
fping -a -g 192.168.1.0/24 2>/dev/null

# 경로 + 손실률 (보고서)
mtr -r -c 100 example.com

# TCP 핑
while true; do nc -zw 2 host 443 && echo "$(date) OK" || echo "$(date) FAIL"; sleep 1; done

# 특정 인터페이스로
ping -I eth1 -c 4 host

# IPv6 도달성
ping -6 -c 4 example.com
```

## 31.10 함정

| 함정 | 대처 |
|------|------|
| ICMP 만 차단 → ping 안 됨 | TCP 핑 (`nc`, `hping3`, `mtr -T`) |
| 중간 홉이 `* * *` 인데 통과 | 정상. 마지막 홉 응답이 핵심 |
| Wi-Fi 파워 세이브 → 첫 ping 느림 | -i 짧게, 워밍업 후 측정 |
| MTU 문제 | `-M do -s SIZE` 로 진단 |
| DNS 가 느려 ping 가 느려 보임 | `-n` (또는 IP 직접) |
| flood ping 으로 차단당함 | 운영망에서 절대 금지 |

다음 챕터: [제32장]

\newpage

---


# 32. dig, nslookup, host — DNS 조회

> 이름이 IP 로 어떻게 변하는지. 어디서 막히는지.

## 32.1 도구 비교

| 도구 | 권장도 | 특징 |
|------|--------|------|
| `dig` (bind-utils) | **★ 권장** | 가장 자세함, 자동화 친화 |
| `host` | 간단 | 빠른 한 줄 결과 |
| `nslookup` | 호환성 | 구식, 인터랙티브 가능 |
| `resolvectl` | systemd | systemd-resolved 의 정공법 |
| `getent hosts` | nsswitch | hosts/ldap 통합 |

```bash
sudo apt install dnsutils      # debian
sudo dnf install bind-utils    # rhel
```

## 32.2 dig 기본

```bash
dig example.com                       # A
dig example.com AAAA                  # IPv6
dig example.com MX
dig example.com NS
dig example.com TXT
dig example.com ANY                   # 거의 안 쓰임 (rfc8482)
dig -x 1.1.1.1                        # 역방향
dig @8.8.8.8 example.com              # 특정 DNS 서버
dig +short example.com                # 결과만
dig +noall +answer example.com        # answer 섹션만
dig +trace example.com                # 루트부터 따라감
dig +tcp example.com                  # TCP 강제
dig +dnssec example.com               # DNSSEC RRSIG 포함
dig +nocmd +noall +answer +stats example.com
```

### 출력 섹션

```
;; QUESTION SECTION:
;example.com.   IN  A

;; ANSWER SECTION:
example.com. 300 IN A 93.184.216.34

;; AUTHORITY SECTION:
example.com. 86400 IN NS a.iana-servers.net.

;; ADDITIONAL SECTION:
a.iana-servers.net. 86400 IN A 199.43.135.53
```

| 섹션 | 의미 |
|------|------|
| QUESTION | 우리가 물은 것 |
| ANSWER | 답 |
| AUTHORITY | 권한 NS 서버 |
| ADDITIONAL | 추가 (글루 레코드 등) |

### dig 자주 쓰는 옵션

| 옵션 | 의미 |
|------|------|
| `+short` | 답 한 줄 |
| `+noall +answer` | ANSWER 만 |
| `+trace` | 루트→TLD→권한 |
| `+tcp` | TCP |
| `+dnssec` | DNSSEC |
| `+norecurse` | 재귀 비활성 (권한 NS 직접 조사) |
| `+stats` | 통계 |
| `+nocmd` | 명령 헤더 끔 |
| `+nocomments` | 주석 끔 |
| `-p PORT` | 포트 |
| `-b ADDR` | 출발지 IP |
| `+timeout=N` | 타임아웃 |
| `+retry=N` | 재시도 |
| `-4` `-6` | IP 버전 |

### 다중 쿼리

```bash
dig example.com A example.com AAAA example.com MX
```

### 자동화 친화 한 줄

```bash
IP=$(dig +short A example.com | head -1)
MX=$(dig +short MX example.com | sort -n | head -1 | awk '{print $2}')
```

## 32.3 trace — 위임 추적

```bash
dig +trace example.com
```

루트(`.`) → TLD(`.com.`) → 권한 NS → 답. DNS 위임이 어디서 깨지는지 한눈에.

## 32.4 host — 간단판

```bash
host example.com
host -t MX example.com
host -t TXT example.com
host -a example.com           # all (잘 안 보임)
host -v example.com           # verbose
host 1.1.1.1                  # 역방향
host example.com 8.8.8.8      # 특정 서버
```

빠르고 깔끔.

## 32.5 nslookup — 호환

```bash
nslookup example.com
nslookup example.com 8.8.8.8
nslookup -type=MX example.com

# 인터랙티브
nslookup
> server 8.8.8.8
> set type=AAAA
> example.com
> exit
```

신규 작성에 굳이 쓸 필요 없지만 윈도/오래된 시스템에서 만남.

## 32.6 resolvectl (systemd-resolved)

```bash
resolvectl status
resolvectl query example.com
resolvectl query example.com --type=AAAA
resolvectl statistics
resolvectl reset-statistics
resolvectl flush-caches
sudo resolvectl dns eth0 1.1.1.1 8.8.8.8
```

systemd-resolved 가 도는 환경에선 이게 진짜 동작 경로.

## 32.7 getent — nsswitch 기반

```bash
getent hosts example.com
getent ahosts example.com         # 모든 주소
getent hosts 1.1.1.1
```

`/etc/nsswitch.conf` 의 hosts 룰을 따른다 (`files dns` 등). `/etc/hosts` 우선이라면 그게 답으로 나옴.

## 32.8 자주 쓰는 패턴

### CNAME 체인

```bash
dig +short www.example.com
# www.example.com → cdn.example.net → 1.2.3.4
```

`+short` 이 모든 단계를 차례로 출력.

### 권한 NS 한테 직접 묻기 (캐시 무시)

```bash
NS=$(dig +short NS example.com | head -1)
dig @"$NS" +norecurse example.com
```

DNS 캐시 문제 의심 시 권한에 직접.

### TTL 확인

```bash
dig example.com | sed -n '/ANSWER SECTION/,/^$/p'
# example.com.  300  IN  A  93.184.216.34
```

`300` 이 TTL. 0 에 가까우면 빠르게 변경 가능.

### MX 우선순위

```bash
dig +short MX example.com | sort -n
# 10 mail1.example.com.
# 20 mail2.example.com.
```

### SPF / DKIM / DMARC

```bash
dig +short TXT example.com | sed -n '/v=spf1/p'
dig +short TXT default._domainkey.example.com
dig +short TXT _dmarc.example.com
```

### 내가 쓰는 DNS 서버

```bash
resolvectl status | sed -n '/DNS Servers/p'
cat /etc/resolv.conf
```

## 32.9 DNSSEC

```bash
dig +dnssec example.com
# AD 플래그가 있으면 검증됨
```

```
;; flags: qr rd ra ad; QUERY: 1, ...
                    ^
```

`ad` = authenticated data.

## 32.10 zone transfer (보안 점검)

```bash
dig @ns.example.com example.com AXFR
# 권한 서버가 transfer 허용 안 한다면 거절됨 (보통 정상)
```

운영 NS 가 AXFR 누구에게나 허용하면 정보 유출. 점검용.

## 32.11 자주 쓰는 한 줄

```bash
# 빠른 IP
dig +short example.com | head -1

# IPv4 + IPv6 한 번에
dig example.com A AAAA +short

# DNS 응답 시간
dig example.com | sed -n 's/.*Query time: //p'

# 캐시 우회 (권한 NS 직조회)
NS=$(dig +short NS example.com | head -1)
dig @"$NS" +norecurse +short example.com

# 특정 DNS 서버 응답 차이
for s in 1.1.1.1 8.8.8.8 9.9.9.9; do
  printf "%-12s %s\n" "$s" "$(dig @"$s" +short example.com | head -1)"
done

# A 레코드 변경 감지 (모니터)
while true; do
  IP=$(dig +short example.com | head -1)
  echo "$(date +%H:%M:%S) $IP"
  sleep 30
done

# 역방향 (PTR) 일괄
for ip in 1.1.1.1 8.8.8.8; do
  printf "%s %s\n" "$ip" "$(dig +short -x "$ip")"
done

# DNS 응답 / 단순한 가용성 체크
dig +short +tries=1 +time=2 example.com >/dev/null && echo OK || echo FAIL
```

## 32.12 함정

| 함정 | 대처 |
|------|------|
| `nslookup` 결과와 `dig` 가 다름 | 둘이 다른 라이브러리 사용 → `dig` 신뢰 |
| 캐시 때문에 변경 안 보임 | TTL 기다리거나 권한 NS 직접 |
| /etc/hosts 가 우선 | `getent hosts`로 실제 OS 동작 확인 |
| systemd-resolved 가 가운데 | `resolvectl flush-caches`, `resolvectl status` |
| NXDOMAIN vs SERVFAIL 구분 | 첫째는 없음, 둘째는 NS 자체 문제 |
| AAAA 만 응답하는 호스트 | `dig AAAA` 명시 |
| DNSSEC 잘못된 서명 | `+dnssec` 로 ad 플래그 확인 |

다음 챕터: [제33장]

\newpage

---


# 33. nc (netcat) 와 socat — 만능 네트워크 도구

> "TCP 의 cat". 포트 테스트, 임시 서버, 파일 전송, 터널까지.

## 33.1 nc 종류

`nc` 는 여러 구현체가 있다. 옵션이 미세하게 다름.

| 구현 | 패키지 | 특징 |
|------|--------|------|
| GNU netcat | `netcat-traditional` | 클래식 |
| OpenBSD netcat | `netcat-openbsd` | 흔히 default, `-N` 등 |
| Ncat (Nmap) | `nmap` | TLS, IPv6, 풍부 |
| BusyBox nc | 임베디드 | 최소 |

```bash
sudo apt install netcat-openbsd     # 또는 -traditional, ncat
```

`nc -h` 로 어떤 구현인지 확인.

## 33.2 nc 기본 — 포트 도달성

```bash
nc -zv host 80                # zero I/O verbose
nc -zvw 3 host 443            # 3초 타임아웃
nc -uzv host 53               # UDP
nc -zv host 20-25             # 포트 범위 (OpenBSD)

# 다중 포트 한 줄
for p in 22 80 443; do
  nc -zvw 2 host $p
done
```

## 33.3 임시 클라이언트 / 서버

### 듣기

```bash
nc -l 9999                    # 포트 9999 listen (한 번)
nc -lk 9999                   # keep-listening (Ncat / OpenBSD)
nc -l -p 9999                 # GNU traditional
```

### 보내기

```bash
nc host 9999
# 입력하는 줄이 그대로 상대에게
```

### 파일 전송

```bash
# 받는 쪽
nc -l 9999 > received.bin

# 보내는 쪽
nc host 9999 < send.bin

# 양방향: 종료 감지가 약함 → -N 옵션 필요
nc -N host 9999 < file
# OpenBSD: -N = stdin EOF 시 종료
```

### tar 와 결합 (디렉토리 전송)

```bash
# 받는 쪽
nc -l 9999 | tar xzf -

# 보내는 쪽
tar czf - dir/ | nc -N host 9999
```

빠르고 SSH 없이도 가능. 신뢰 망 전용.

## 33.4 HTTP/SMTP 수동 (Telnet 대신)

```bash
# HTTP HEAD
{ printf 'HEAD / HTTP/1.1\r\nHost: example.com\r\nConnection: close\r\n\r\n'; } \
  | nc example.com 80

# SMTP banner
nc -C smtp.example.com 25       # -C: CRLF 변환
EHLO me
QUIT
```

OpenBSD nc 는 `-C` 가 CRLF, `-c` 가 (없음). Ncat 은 `-C` 가 같은 의미.

## 33.5 백도어처럼 쓰기 (절대 운영 X, 진단용)

```bash
# 서버 측
nc -l 9999 -e /bin/bash       # 위험 (GNU/Ncat 만 -e)

# 클라이언트
nc host 9999
```

OpenBSD nc 는 보안상 `-e` 옵션이 빠져 있음. **운영 환경에 절대 두지 말 것**.

## 33.6 채팅 / 키 입력 테스트

```bash
# 좌
nc -l 9999

# 우
nc localhost 9999
```

서로 입력이 그대로 전달된다.

## 33.7 ncat (Nmap) 의 강점

```bash
ncat --ssl host 443           # TLS
ncat --ssl-verify --ssl-cert client.crt --ssl-key client.key host 443
ncat -l --ssl --ssl-cert s.crt --ssl-key s.key 443

ncat -l 9999 --keep-open
ncat -l --broker 9999         # 다중 클라 채팅 브로커
ncat -l --chat 9999           # 채팅 모드
ncat -e /bin/bash --allow 10.0.0.0/8 -l 9999
ncat --proxy proxy:3128 host 443
ncat --udp -l 1234
```

`ncat` 이 `nc` 의 다음 세대. 가능하면 그쪽으로.

## 33.8 socat — 더 강력한 형제

socat 은 두 데이터 스트림을 양방향으로 연결한다. 거의 모든 프로토콜 / 파일 / 디바이스 / 소켓 → 모든 것.

```bash
sudo apt install socat
```

기본 형식:

```
socat [옵션] ADDRESS1 ADDRESS2
```

데이터가 ADDRESS1 ↔ ADDRESS2 로 흘러간다.

### 자주 쓰는 ADDRESS 종류

| ADDRESS | 의미 |
|---------|------|
| `STDIO` 또는 `-` | 표준 입출력 |
| `TCP:host:port` | TCP 연결 |
| `TCP-LISTEN:port` | TCP listen |
| `UDP:host:port` | UDP 보내기 |
| `UDP-LISTEN:port` | UDP listen |
| `UNIX-CONNECT:/path` | Unix 도메인 |
| `UNIX-LISTEN:/path` | |
| `OPEN:/file,creat,append` | 파일 |
| `EXEC:cmd` | 명령 실행 |
| `SYSTEM:cmd` | 셸로 |
| `PTY` | 가상 터미널 |
| `OPENSSL:host:port` | TLS |
| `OPENSSL-LISTEN:port` | TLS 서버 |
| `SOCKS4:proxy:host:port` | SOCKS |

### 예제 — 포트 포워딩

```bash
# 8080 으로 들어온 걸 internal:80 으로
socat TCP-LISTEN:8080,fork,reuseaddr TCP:internal:80

# 외부 인터페이스에 바인드
socat TCP-LISTEN:8080,bind=0.0.0.0,fork,reuseaddr TCP:internal:80

# UDP 포워딩
socat UDP-LISTEN:5353,fork UDP:8.8.8.8:53
```

`fork` 가 없으면 한 연결만 처리하고 종료.

### 예제 — 시리얼 ↔ TCP

```bash
sudo socat /dev/ttyUSB0,b115200,raw,echo=0 TCP-LISTEN:9999,fork,reuseaddr
```

원격에서 `nc host 9999` 로 시리얼 콘솔 접속.

### 예제 — TLS 추가/제거

```bash
# 평문 서버 앞에 TLS 종단
socat OPENSSL-LISTEN:443,cert=server.pem,verify=0,fork \
      TCP:localhost:8080

# TLS 백엔드를 평문으로
socat TCP-LISTEN:8080,fork \
      OPENSSL:secure.example.com:443,verify=1
```

### 예제 — 양방향 데이터 복제 (브로드캐스트)

```bash
socat -u STDIO TCP:host1:9999 &
socat -u STDIO TCP:host2:9999 &
```

### 예제 — 파일 ↔ TCP

```bash
# 파일 내용을 TCP 로 흘림
socat OPEN:bigfile,rdonly TCP:host:9999

# TCP 로 들어오는 데이터 → 파일
socat -u TCP-LISTEN:9999 OPEN:received.bin,creat,trunc
```

### 예제 — 명령 노출 (조심)

```bash
# 내가 8888 에 접속하면 셸이 뜸 (절대 운영 X)
socat TCP-LISTEN:8888,fork EXEC:/bin/bash,pty,stderr,sigint,setsid,sane
```

진단 / 격리 환경 전용.

### 예제 — 가상 시리얼 페어 (개발용)

```bash
socat -d -d pty,raw,echo=0 pty,raw,echo=0
# 두 개의 /dev/pts/N 을 만들어 서로 연결
# 한 쪽 프로그램이 시리얼 통신하면 다른 쪽도 받음
```

## 33.9 SSL/TLS 진단 — openssl s_client

`nc` 는 TLS 안 됨. TLS 진단은:

```bash
openssl s_client -connect host:443 -servername host

# 짧게
echo | openssl s_client -connect host:443 2>/dev/null | openssl x509 -noout -dates -subject

# CONNECT 후 STARTTLS (smtp)
openssl s_client -connect smtp:25 -starttls smtp
```

## 33.10 자주 쓰는 한 줄

```bash
# 포트 스캔 (단순)
for p in 22 80 443 3306 8080; do
  nc -zvw 2 host $p 2>&1 | sed -n '/succeeded\|open/p'
done

# 임시 HTTP 서버
while true; do
  printf 'HTTP/1.1 200 OK\r\nContent-Length: 5\r\n\r\nhello' | nc -lN 8000
done
# Python 이 더 편함:
python3 -m http.server 8000

# 임시 페이로드 받기
nc -lk 9000 | tee received.log

# 파일을 빠르게 옮기기
# 받는 쪽 (먼저)
nc -l 9999 > out.bin
# 보내는 쪽
nc -N host 9999 < in.bin

# UDP 패킷 한 번 보내기
echo "ping" | nc -u -w 1 host 5000

# socat 으로 unix 소켓 → tcp 노출
socat TCP-LISTEN:8080,fork UNIX-CONNECT:/var/run/myapp.sock

# socat 으로 TLS → 평문 변환
socat OPENSSL-LISTEN:8443,cert=cert.pem,key=key.pem,verify=0,fork TCP:localhost:8080

# 빠른 채팅 (LAN)
# A
nc -l 9999
# B
nc A 9999
```

## 33.11 보안 / 함정

| 함정 | 대처 |
|------|------|
| `nc -e` 백도어 노출 | OpenBSD nc는 `-e` 없음. ncat 의 `--allow` 사용 |
| 임시 listen 이 외부에 노출 | `127.0.0.1:` 바인드 또는 방화벽 |
| EOF 후에도 안 끊김 | OpenBSD `-N`, ncat `--send-only` |
| 큰 파일 전송 중 끊김 | rsync over SSH 가 안전 |
| 평문 채널 | TLS 필요 시 ncat/socat |
| socat 여러 fork 가 좀비 | `reuseaddr,fork` + 종료 시그널 잘 처리 |
| 라인 끝 차이 | nc `-C` (CRLF) 옵션 |

다음 챕터: [제34장]

\newpage

---


# 34. tcpdump — 패킷 캡처

> 네트워크에서 진짜 무엇이 흐르는지 본다. 마지막 디버깅 무기.

## 34.1 설치 / 권한

```bash
sudo apt install tcpdump
sudo dnf install tcpdump
```

거의 항상 root 권한 필요. capability 부여로 일반 사용자도:

```bash
sudo setcap cap_net_raw,cap_net_admin=eip $(which tcpdump)
```

## 34.2 기본

```bash
sudo tcpdump                          # 임의 인터페이스
sudo tcpdump -i eth0                  # 인터페이스 지정
sudo tcpdump -i any                   # 모든
sudo tcpdump -D                       # 인터페이스 목록
sudo tcpdump -i eth0 -n               # DNS 안 풀기
sudo tcpdump -i eth0 -nn              # 포트 이름도 안 풀기
sudo tcpdump -i eth0 -c 10            # 10개만
sudo tcpdump -i eth0 -v / -vv / -vvv  # 자세히
sudo tcpdump -i eth0 -w cap.pcap      # 파일 저장 (Wireshark 용)
sudo tcpdump -r cap.pcap              # 파일 읽기
sudo tcpdump -i eth0 -s 0             # snaplen 무한 (전체 패킷)
sudo tcpdump -i eth0 -X               # hex + ASCII
sudo tcpdump -i eth0 -A               # ASCII (HTTP 등)
sudo tcpdump -i eth0 -e               # 이더넷 헤더
sudo tcpdump -i eth0 -tt              # 타임스탬프 unix
sudo tcpdump -i eth0 -tttt            # 사람용 시간
sudo tcpdump -i eth0 -G 60 -w cap-%F-%H-%M.pcap  # 60초마다 새 파일
sudo tcpdump -i eth0 -C 100 -W 5 -w cap.pcap     # 100MB 마다 회전, 5개 보관
```

## 34.3 BPF 필터 — 핵심

| 필터 | 의미 |
|------|------|
| `host 1.2.3.4` | 출발지/도착지 IP |
| `src host 1.2.3.4` | 출발지 |
| `dst host 1.2.3.4` | 도착지 |
| `net 10.0.0.0/8` | 네트워크 |
| `port 443` | 출/도착 포트 |
| `src port 80` / `dst port 80` | |
| `portrange 8000-9000` | 범위 |
| `tcp` / `udp` / `icmp` / `arp` | 프로토콜 |
| `ether host MAC` | MAC |
| `vlan 10` | VLAN |
| `not`, `and`, `or` | 논리 |
| `()` | 그룹 (이스케이프 또는 따옴표) |

```bash
sudo tcpdump -i eth0 -nn 'tcp port 443'
sudo tcpdump -i eth0 -nn 'host 1.2.3.4 and port 80'
sudo tcpdump -i eth0 -nn 'src net 10.0.0.0/8 and dst port 443'
sudo tcpdump -i eth0 -nn 'tcp and (port 80 or port 443)'
sudo tcpdump -i eth0 -nn 'not arp and not port 22'
sudo tcpdump -i eth0 -nn 'icmp[icmptype]=icmp-echo'   # ping 만
sudo tcpdump -i eth0 -nn 'tcp[tcpflags] & (tcp-syn|tcp-fin) != 0'
sudo tcpdump -i eth0 -nn 'tcp[tcpflags] & tcp-syn != 0 and tcp[tcpflags] & tcp-ack = 0'  # SYN only
sudo tcpdump -i eth0 -nn 'tcp[((tcp[12]&0xf0)>>2):4] = 0x47455420'  # GET 요청
```

## 34.4 출력 읽기

```
12:34:56.789012 IP 192.168.1.10.50000 > 1.2.3.4.443: Flags [S], seq 1234567890, win 64240, options [...], length 0
```

| 필드 | 의미 |
|------|------|
| `12:34:56...` | 타임스탬프 |
| `IP` | 프로토콜 |
| `src.port > dst.port` | 출/도착 |
| `Flags [S]` | SYN. `[.]`=ACK, `[F]`=FIN, `[R]`=RST, `[P]`=PSH, `[S.]`=SYN-ACK |
| `seq` | 시퀀스 번호 |
| `ack` | ACK |
| `win` | 윈도우 크기 |
| `length` | 페이로드 |

### TCP 핸드셰이크 보기

```bash
sudo tcpdump -i any -nn 'tcp port 80 and host example.com'
```

```
[S]   client → server   SYN
[S.]  server → client   SYN+ACK
[.]   client → server   ACK
[P.]  client → server   GET / HTTP/1.1...
```

## 34.5 자주 쓰는 시나리오

### "왜 응답이 안 와?"

```bash
sudo tcpdump -i any -nn 'host 1.2.3.4 and port 443' -c 50
# SYN 만 가고 SYN-ACK 안 옴 → 방화벽 또는 라우팅
# SYN-ACK 까지는 오는데 응답이 RST → 서버 측 차단
```

### HTTP 평문 보기

```bash
sudo tcpdump -i eth0 -A -s 0 'tcp port 80'
```

### DNS 보기

```bash
sudo tcpdump -i any -nn 'udp port 53'
sudo tcpdump -i any -nn -s 0 -X 'udp port 53'
```

### ICMP / ping

```bash
sudo tcpdump -i any -nn icmp
```

### ARP

```bash
sudo tcpdump -i eth0 -nn arp
```

### 특정 호스트와 모든 통신

```bash
sudo tcpdump -i any -nn host 1.2.3.4
```

## 34.6 파일로 저장 → Wireshark 로 분석

```bash
sudo tcpdump -i eth0 -s 0 -w cap.pcap 'host 1.2.3.4'
# Ctrl+C
ls -lh cap.pcap
```

로컬에서 wireshark, 또는 원격에서 캡처해 가져오기:

```bash
sudo tcpdump -i eth0 -s 0 -w - 'host 1.2.3.4' \
  | ssh -C analyst@laptop "cat > cap.pcap"
```

또는 라이브 스트리밍:

```bash
ssh server sudo tcpdump -i eth0 -U -w - 'host 1.2.3.4' \
  | wireshark -k -i -
```

## 34.7 대용량 캡처 — 파일 회전

```bash
sudo tcpdump -i eth0 -G 3600 -w 'cap-%F-%H.pcap' -W 24 'tcp'
# 1시간마다 새 파일, 24개 유지 (-W = limit, 라운드로빈)

sudo tcpdump -i eth0 -C 100 -W 10 -w cap.pcap 'tcp'
# 100MB 마다 회전, cap.pcap0 ~ cap.pcap9
```

`-Z user` 로 권한 낮춤:

```bash
sudo tcpdump -i eth0 -Z tcpdump -G 60 -w cap-%F.pcap
```

## 34.8 tshark — Wireshark CLI

```bash
sudo apt install tshark
sudo tshark -i eth0 -Y 'http.request' -T fields -e ip.src -e http.host -e http.request.uri
```

복잡한 디스플레이 필터는 tshark 가 강력. tcpdump 가 못 보는 protocol 도 디코드.

## 34.9 dumpcap / termshark

- `dumpcap` — Wireshark 의 캡처 엔진 (root 부담 적음)
- `termshark` — 터미널 GUI Wireshark (htop 처럼)

## 34.10 팁 / 함정

| 함정 | 대처 |
|------|------|
| 패킷이 잘려 보임 | `-s 0` 로 전체 캡처 |
| 디스크 폭주 | `-C`, `-W`, `-G` 로 회전, 필터 좁힘 |
| 자기 자신 ssh 트래픽 캡처 → 무한 루프 비슷 | `not port 22` 로 제외 |
| 가상 인터페이스 (docker0, vethX) 안 잡힘 | `-i any` 또는 정확한 인터페이스 |
| 컨테이너 안 트래픽 | host nsenter / 컨테이너 안에서 |
| TLS 라 본문 안 보임 | TLS 종단 후 또는 키 export 로 wireshark 복호화 |
| `tcpdump: any: ... not supported` | 옛 커널, `lo` `eth0` 등 직접 |
| 시간 동기 안 됨 | NTP, `-tttt` 로 절대시각 |

## 34.11 자주 쓰는 한 줄 모음

```bash
# 새 SYN 만 (스캔 / 신규 연결 흐름)
sudo tcpdump -i any -nn 'tcp[tcpflags] & tcp-syn != 0 and tcp[tcpflags] & tcp-ack = 0'

# DNS 응답 안 오는 호스트
sudo tcpdump -i any -nn 'udp port 53'

# 80 / 443 만
sudo tcpdump -i any -nn 'tcp port 80 or tcp port 443'

# 1.2.3.4 와 통신만
sudo tcpdump -i any -nn host 1.2.3.4

# 자기 호스트 빼고
sudo tcpdump -i any -nn 'not host '"$(hostname -I | awk '{print $1}')"

# 큰 패킷
sudo tcpdump -i eth0 -nn 'greater 1000'

# RST 폭증 의심
sudo tcpdump -i any -nn 'tcp[tcpflags] & tcp-rst != 0'

# 1분만 캡처해서 저장
sudo timeout 60 tcpdump -i eth0 -s 0 -w 1min.pcap
```

다음 챕터: [제35장]

\newpage

---


# 35. nmap — 포트 스캐닝과 네트워크 검색

> "이 호스트들 중 무엇이 살아있고 어떤 서비스가 돌아가나?"

## 35.1 윤리 / 합법

`nmap` 은 정찰 도구다. **반드시 자신이 관리/허가받은 네트워크에만** 사용. 외부 호스트에 무단 스캔은 위법.

## 35.2 설치

```bash
sudo apt install nmap
```

## 35.3 호스트 발견 (Ping 스캔)

```bash
sudo nmap -sn 192.168.1.0/24       # 살아있는 호스트만
sudo nmap -sn -PE 10.0.0.0/24      # ICMP echo
sudo nmap -sn -PS22,80,443 host    # TCP SYN ping
sudo nmap -sn -PA22,80,443 host    # TCP ACK ping
sudo nmap -sn -PU53 host           # UDP ping
sudo nmap -sn -PR host             # ARP (LAN 내부)
sudo nmap -Pn host                 # 핑 생략 (방화벽 우회)
sudo nmap -n 192.168.1.0/24        # DNS 안 풀기
```

LAN 내부에선 ARP가 가장 빠르고 정확.

## 35.4 포트 스캔 종류

| 스캔 | 옵션 | 설명 |
|------|------|------|
| TCP SYN (stealth) | `-sS` | **기본 권장**. 핸드셰이크 미완 (root) |
| TCP connect | `-sT` | 일반 connect(). 권한 없을 때 기본 |
| UDP | `-sU` | 매우 느림 |
| FIN/Xmas/Null | `-sF`/`-sX`/`-sN` | 방화벽 우회 시도 |
| ACK | `-sA` | 방화벽 룰 매핑 |
| Window | `-sW` | |
| TLS handshake | `-sV` 와 함께 |

```bash
sudo nmap -sS host                 # 기본
sudo nmap -sS -p 80,443 host       # 특정 포트
sudo nmap -sS -p 1-1000 host       # 범위
sudo nmap -sS -p- host             # 모든 포트 (1-65535)
sudo nmap -sS --top-ports 100 host
sudo nmap -sU -p 53,123 host       # UDP
sudo nmap -sS -F host              # fast (top 100)
```

## 35.5 서비스 / 버전 / OS 감지

```bash
sudo nmap -sV host                  # 버전
sudo nmap -sV --version-intensity 9 host
sudo nmap -O host                   # OS 추측
sudo nmap -A host                   # 종합 (-O -sV --traceroute --script=default)
```

`-A` 는 시끄럽다. 운영 환경에선 단계적으로.

## 35.6 NSE — Nmap Scripting Engine

```bash
sudo nmap --script=default host
sudo nmap --script=safe host
sudo nmap --script=vuln host        # 취약점 점검
sudo nmap --script=ssl-cert -p 443 host
sudo nmap --script=ssl-enum-ciphers -p 443 host
sudo nmap --script=http-title -p 80,443 host
sudo nmap --script=smb-os-discovery -p 445 host
sudo nmap --script=dns-brute --script-args=dns-brute.domain=example.com
```

스크립트 카테고리: `auth`, `default`, `discovery`, `safe`, `vuln`, `intrusive`, `brute`, `dos`, `exploit`, `malware`.

```bash
ls /usr/share/nmap/scripts/ | head
nmap --script-help=ssl-enum-ciphers
```

## 35.7 출력 / 저장

```bash
sudo nmap -sS -oN scan.txt host             # 사람용 텍스트
sudo nmap -sS -oG scan.gnmap host           # grep 친화
sudo nmap -sS -oX scan.xml host             # XML
sudo nmap -sS -oA scan host                 # 세 형식 모두
sudo nmap -sS -v host                       # verbose
sudo nmap -sS -vv host                      # 더
sudo nmap -sS -d host                       # 디버그
```

## 35.8 속도 / 정중함

`-T0`(paranoid) ~ `-T5`(insane). 기본은 `-T3`. 운영 망에선 `-T2` 까지.

```bash
sudo nmap -sS -T4 host
sudo nmap --max-rate 100 host
sudo nmap --min-rate 1000 host
sudo nmap --max-retries 1 host
sudo nmap --host-timeout 30s host
sudo nmap --scan-delay 1s host
```

큰 망 스캔은 분할:

```bash
sudo nmap -sS -T4 -iL targets.txt -oA scan
```

`targets.txt`:
```
192.168.1.0/24
10.0.0.0/16
example.com
```

## 35.9 자주 쓰는 한 줄

```bash
# LAN 살아있는 호스트
sudo nmap -sn 192.168.1.0/24

# 빠른 검색 (top 100 포트)
sudo nmap -sS -F 192.168.1.0/24

# 모든 포트 + 버전 + OS
sudo nmap -sS -p- -sV -O host

# 특정 호스트가 어떤 웹 서버
sudo nmap -p 80,443 --script=http-headers,http-title,ssl-cert host

# SSL/TLS 점검
sudo nmap --script=ssl-enum-ciphers -p 443 host

# SMB / 파일 공유 식별
sudo nmap -p 445 --script=smb-os-discovery,smb-protocols host

# 네트워크 라우터 식별
sudo nmap -p 161 --script=snmp-info host

# 빠른 그리드 결과 → grep
sudo nmap -sS -F 10.0.0.0/24 -oG - | sed -n '/Ports:/p'
```

## 35.10 ndiff — 두 스캔 비교

```bash
sudo nmap -sS host -oX before.xml
# 시간 경과
sudo nmap -sS host -oX after.xml
ndiff before.xml after.xml
```

새 포트 / 사라진 포트 변화 추적.

## 35.11 zenmap

GUI. 결과 시각화에 좋다. 운영 도구로는 CLI 가 자동화에 어울림.

## 35.12 흔한 오해

| 오해 | 사실 |
|------|------|
| `-Pn` 면 항상 정확 | 핑이 차단됐다고 가정. 다만 호스트가 없을 때도 모든 포트 스캔 → 시간 큼 |
| 모든 포트 스캔이 빠름 | `-p-` 는 65535 포트 전부, 매우 느림. 분할 |
| 결과가 항상 정확 | 방화벽/IDS 가 결과를 변형 |
| 외부에서 무단 스캔 OK | **위법**. 자기 자산만 |

## 35.13 자기 점검 (체크리스트)

```bash
# 자기 호스트의 외부 노출 점검
sudo nmap -sS -p- -T4 $(hostname -I | awk '{print $1}')

# LAN 내 다른 호스트
sudo nmap -sn 192.168.1.0/24

# 한 시간 후 다시 → 변화
sudo nmap -sS -F host -oX scan-now.xml
# 매주 cron 으로 ndiff
```

다음 챕터: [제36장]

\newpage

---


# 36. iptables / nftables / ufw — 방화벽

> 패킷 룰을 어디에서 어떻게 적용할까. 표준은 nftables, 현실은 iptables, 데스크탑은 ufw.

## 36.1 큰 그림

| 도구 | 역할 |
|------|------|
| `iptables` | 전통 방화벽. xt_* 모듈 |
| `nftables` | iptables 의 후계자 (nft 명령) |
| `ufw` | iptables 위 단순 wrapper (Ubuntu) |
| `firewalld` | nftables/iptables 위 zone 기반 (RHEL) |

새 시스템은 보통 nftables 위에 ufw / firewalld 가 올라가 있다.

## 36.2 iptables 핵심 개념

- **테이블**: filter (기본), nat, mangle, raw, security
- **체인**: INPUT, OUTPUT, FORWARD, PREROUTING, POSTROUTING
- **타깃**: ACCEPT, DROP, REJECT, LOG, RETURN, JUMP, MASQUERADE, SNAT, DNAT 등

```
[들어옴] → PREROUTING → [라우팅] → INPUT → [로컬 프로세스]
                                  → FORWARD → POSTROUTING → [나감]
[로컬]  → OUTPUT  → POSTROUTING → [나감]
```

## 36.3 iptables 기본 명령

```bash
sudo iptables -L                       # 목록
sudo iptables -L -n -v --line-numbers
sudo iptables -L INPUT -nv
sudo iptables -t nat -L -n
sudo iptables -F                       # 모두 비움 (조심)
sudo iptables -F INPUT
sudo iptables -X                       # 사용자 체인 제거
sudo iptables -Z                       # 카운터 0
```

### 룰 추가

```bash
# 일반 패턴
sudo iptables -A CHAIN [매칭] -j TARGET

# 22 허용
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# 80, 443 허용
sudo iptables -A INPUT -p tcp -m multiport --dports 80,443 -j ACCEPT

# 특정 IP만 SSH
sudo iptables -A INPUT -p tcp --dport 22 -s 10.0.0.0/8 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 22 -j DROP

# 로컬루프 허용
sudo iptables -A INPUT -i lo -j ACCEPT

# 기존 연결 응답 허용
sudo iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# ICMP 허용
sudo iptables -A INPUT -p icmp -j ACCEPT

# 기본 정책: DROP (룰 다 추가한 뒤에)
sudo iptables -P INPUT DROP
sudo iptables -P FORWARD DROP
sudo iptables -P OUTPUT ACCEPT
```

### 룰 삭제 / 삽입

```bash
sudo iptables -L INPUT --line-numbers
sudo iptables -D INPUT 3            # 3번 룰 삭제
sudo iptables -I INPUT 1 -i lo -j ACCEPT   # 1번 위치에 삽입
```

### NAT (포트 포워딩)

```bash
# 외부 8080 → 내부 80
sudo iptables -t nat -A PREROUTING -p tcp --dport 8080 \
    -j DNAT --to-destination 10.0.0.5:80

# Masquerade (NAT 게이트웨이)
sudo iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE

# IP 포워딩 활성화
sudo sysctl -w net.ipv4.ip_forward=1
echo 'net.ipv4.ip_forward=1' | sudo tee -a /etc/sysctl.conf
```

### 영구 저장

```bash
# Debian
sudo apt install iptables-persistent
sudo netfilter-persistent save
sudo netfilter-persistent reload
# 위치: /etc/iptables/rules.v4, rules.v6

# RHEL (구식)
sudo service iptables save
# 위치: /etc/sysconfig/iptables

# 수동
sudo iptables-save > /etc/iptables/rules.v4
sudo iptables-restore < /etc/iptables/rules.v4
```

## 36.4 자주 쓰는 매처

| 매처 | 설명 |
|------|------|
| `-p tcp/udp/icmp` | 프로토콜 |
| `--dport`, `--sport` | 포트 |
| `-m multiport --dports 80,443` | 다중 포트 |
| `-s`, `-d` | 출/도착 IP |
| `-i`, `-o` | in/out 인터페이스 |
| `-m state --state ...` | 구식 |
| `-m conntrack --ctstate NEW,ESTAB...` | 연결 추적 |
| `-m limit --limit 10/s` | 속도 제한 |
| `-m recent` | 최근 본 IP 추적 |
| `-m string --string "..."` | 페이로드 검사 |
| `-m owner --uid-owner USER` | 로컬 OUTPUT 에서 사용자 |
| `-m time --timestart 09:00 --timestop 18:00` | 시간대 |

## 36.5 흔한 룰 셋 — 작은 서버

```bash
#!/bin/bash
set -e

# 정책 일단 ACCEPT 로 (정의하다 SSH 끊김 방지)
iptables -P INPUT ACCEPT
iptables -P FORWARD ACCEPT
iptables -P OUTPUT ACCEPT

# 비우기
iptables -F
iptables -X
iptables -t nat -F
iptables -t mangle -F

# loopback
iptables -A INPUT -i lo -j ACCEPT

# 기존 연결
iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# ICMP
iptables -A INPUT -p icmp -j ACCEPT

# SSH (브루트포스 보호)
iptables -A INPUT -p tcp --dport 22 -m conntrack --ctstate NEW \
  -m recent --set --name SSH
iptables -A INPUT -p tcp --dport 22 -m conntrack --ctstate NEW \
  -m recent --update --seconds 60 --hitcount 5 --name SSH -j DROP
iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# HTTP/S
iptables -A INPUT -p tcp -m multiport --dports 80,443 -j ACCEPT

# 그 외 차단
iptables -A INPUT -j LOG --log-prefix "iptables-drop: " --log-level 4
iptables -A INPUT -j DROP

# 정책 강화
iptables -P INPUT DROP
iptables -P FORWARD DROP
```

저장:

```bash
sudo iptables-save > /etc/iptables/rules.v4
```

## 36.6 nftables (현대)

```bash
sudo apt install nftables
sudo systemctl enable --now nftables
```

룰 파일 `/etc/nftables.conf`:

```nft
#!/usr/sbin/nft -f
flush ruleset

table inet filter {
    chain input {
        type filter hook input priority filter; policy drop;
        ct state established,related accept
        iif "lo" accept
        ip protocol icmp accept
        tcp dport 22 ct state new limit rate 5/minute accept
        tcp dport { 80, 443 } accept
        log prefix "drop: " counter
    }
    chain forward {
        type filter hook forward priority filter; policy drop;
    }
    chain output {
        type filter hook output priority filter; policy accept;
    }
}
```

```bash
sudo nft -f /etc/nftables.conf
sudo nft list ruleset
sudo nft list table inet filter
sudo nft add rule inet filter input ip saddr 10.0.0.0/8 accept
sudo nft delete rule inet filter input handle 5
```

iptables 룰을 변환:

```bash
iptables-save | iptables-restore-translate -f -
```

## 36.7 ufw — 단순한 frontend

```bash
sudo apt install ufw

sudo ufw status
sudo ufw status verbose
sudo ufw status numbered

# 기본 정책
sudo ufw default deny incoming
sudo ufw default allow outgoing

# 규칙
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow from 10.0.0.0/8 to any port 22
sudo ufw deny from 1.2.3.4
sudo ufw limit ssh                       # 브루트포스 방지

# 활성화
sudo ufw enable

# 비활성/리셋
sudo ufw disable
sudo ufw reset

# 룰 삭제
sudo ufw delete 3                        # 번호로
sudo ufw delete allow 80/tcp             # 같은 룰
```

GUI(gufw) 도 있다. 데스크탑/단순 서버에 OK.

## 36.8 firewalld (RHEL/Fedora)

```bash
sudo systemctl enable --now firewalld

firewall-cmd --state
firewall-cmd --get-active-zones
firewall-cmd --list-all
firewall-cmd --get-services
firewall-cmd --get-default-zone

# 영구 룰 (--permanent + reload)
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --permanent --add-port=8080/tcp
sudo firewall-cmd --permanent --add-source=10.0.0.0/8 --zone=trusted
sudo firewall-cmd --reload

# 일시 룰
sudo firewall-cmd --add-port=8080/tcp
sudo firewall-cmd --remove-port=8080/tcp

# 풍부 룰
sudo firewall-cmd --permanent --add-rich-rule \
  'rule family="ipv4" source address="1.2.3.4" reject'
```

zone 개념: 인터페이스/소스를 zone(public, trusted, dmz...) 에 묶고 zone 별 룰.

## 36.9 fail2ban — 자동 차단

브루트포스 자동 차단. 로그를 보고 일정 시간 차단.

```bash
sudo apt install fail2ban
sudo systemctl enable --now fail2ban
sudo fail2ban-client status
sudo fail2ban-client status sshd
```

`/etc/fail2ban/jail.local`:

```ini
[DEFAULT]
bantime = 1h
findtime = 10m
maxretry = 5

[sshd]
enabled = true
port = ssh
logpath = %(sshd_log)s
backend = systemd
```

## 36.10 디버깅 / 로깅

```bash
# 룰 카운터 (얼마나 매칭?)
sudo iptables -L INPUT -nv

# 0 으로 리셋
sudo iptables -Z INPUT

# LOG 타깃
sudo iptables -A INPUT -p tcp --dport 22 -j LOG --log-prefix "ssh: "

# 로그 위치
sudo journalctl -k | sed -n '/ssh:/p'
sudo dmesg | grep iptables
```

`sysctl` 점검:

```bash
sysctl net.ipv4.conf.all.rp_filter      # 1=리턴 경로 필터
sysctl net.ipv4.tcp_syncookies          # SYN flood 보호
```

## 36.11 함정

| 함정 | 대처 |
|------|------|
| 정책 DROP 으로 두고 SSH 끊김 | 항상 ESTABLISHED 룰 먼저, 정책은 마지막 |
| 영구 저장 안 함 → 재부팅 후 사라짐 | iptables-persistent / nftables.conf |
| 룰 순서 무관하다고 오해 | **위에서부터** 평가, 첫 매치가 결정 |
| ICMP 다 차단 | PMTU 등 깨짐, 핵심 ICMP 는 허용 (echo-reply, fragmentation-needed) |
| docker 가 룰 덮어씀 | docker 가 자체 체인 추가 (DOCKER, DOCKER-USER) |
| ufw 와 docker 충돌 | DOCKER-USER 체인에 룰 추가 |
| nftables 와 iptables 동시 | 한쪽으로 통일 |

## 36.12 자주 쓰는 한 줄

```bash
# 누가 SYN 폭주?
sudo iptables -A INPUT -p tcp --syn -m limit --limit 10/s -j ACCEPT
sudo iptables -A INPUT -p tcp --syn -j DROP

# 특정 국가 차단 (geoip + ipset)
sudo apt install ipset
sudo ipset create cn hash:net
# CN CIDR 목록 추가...
sudo iptables -I INPUT -m set --match-set cn src -j DROP

# DNS amplification 차단
sudo iptables -I INPUT -p udp --dport 53 -m string --string "ANY" --algo bm -j DROP

# SSH 만 특정 IP
sudo iptables -A INPUT -p tcp --dport 22 -s 10.0.0.0/8 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 22 -j DROP

# 임시 차단 1시간 (단순)
sudo iptables -I INPUT -s 1.2.3.4 -j DROP
echo "iptables -D INPUT -s 1.2.3.4 -j DROP" | at now + 1 hour
```

다음 챕터: [제37장]

\newpage

---


# 37. chmod, chown, chgrp, umask — 기본 권한

> rwx · 사용자/그룹/기타. 모든 권한 사고는 여기서 시작.

## 37.1 권한 표기 읽기

```
-rw-r--r--  1 alice  staff  1234 May  7 09:00 file.txt
drwxr-xr-x  3 alice  staff   100 May  7 09:00 dir/
lrwxrwxrwx  1 alice  staff    11 May  7 09:00 link -> file.txt
```

| 위치 | 의미 |
|------|------|
| 1번째 | 파일 종류 (`-`=파일, `d`=디렉토리, `l`=링크, `c`/`b`=캐릭터/블록 디바이스, `p`=파이프, `s`=소켓) |
| 2~4 | 소유자(user) rwx |
| 5~7 | 그룹 rwx |
| 8~10 | 기타(other) rwx |

| 비트 | 파일 | 디렉토리 |
|------|------|----------|
| r | 읽기 | 목록 보기 |
| w | 쓰기 | 항목 추가/삭제 |
| x | 실행 | 진입(`cd`) / 안의 inode 접근 |

> 디렉토리에서 `r` 만 있고 `x` 없으면: 이름은 보이는데 stat 가 안 됨. `x` 만 있고 `r` 없으면: 이름은 못 봐도 정확한 이름으로는 접근 가능.

## 37.2 chmod — 권한 변경

### 8진수 표기

```
r=4, w=2, x=1
rwx=7  rw-=6  r-x=5  r--=4  -wx=3  -w-=2  --x=1  ---=0
```

```bash
chmod 755 file       # rwxr-xr-x
chmod 644 file       # rw-r--r--
chmod 600 file       # rw-------
chmod 700 dir        # rwx------
chmod 777 file       # 위험
chmod 4755 file      # setuid
chmod 2755 dir       # setgid
chmod 1777 /tmp      # sticky
```

### 심볼릭 표기

```
[ugoa] [+-=] [rwxXst]
u=user g=group o=other a=all
+ 추가, - 제거, = 정확히
```

```bash
chmod u+x script.sh
chmod g-w file
chmod o=r file
chmod a+r file
chmod ug=rw,o=r file
chmod -R u+rw,go-rwx ~/secret/

# 디렉토리에만 x (대문자 X)
chmod -R u+rwX,g+rX,o+rX dir/
# → 디렉토리는 x 추가, 일반파일은 (이미 x 있을 때만) x
```

대문자 `X` 가 매우 유용 — 트리에 일괄 적용 시 디렉토리만 들어갈 수 있게.

### 자주 쓰는 매핑

| 의도 | 모드 |
|------|------|
| 일반 파일 | 644 |
| 비밀 파일 (키, 토큰) | 600 |
| 실행 가능한 스크립트 | 755 또는 700 |
| 일반 디렉토리 | 755 |
| 비공개 디렉토리 | 700 |
| 공유 작업 디렉토리 | 1775 (sticky + setgid) |

## 37.3 chown / chgrp — 소유자

```bash
sudo chown alice file
sudo chown alice:dev file              # 사용자:그룹
sudo chown :dev file                    # 그룹만 (= chgrp)
sudo chown -R alice:dev project/
sudo chown --reference=ref file        # ref 와 같은 소유자/그룹
sudo chgrp dev file
sudo chgrp -R dev project/
```

| 옵션 | 의미 |
|------|------|
| `-R` | 재귀 |
| `-h` | 심볼릭 링크 자체 (기본은 따라감) |
| `-H`/`-L`/`-P` | -R 시 링크 처리 |
| `--reference=F` | 다른 파일 참조 |
| `--from=USER` | 현재 소유자가 USER 일 때만 |
| `-c` | 변경된 것만 출력 |
| `-v` | verbose |

## 37.4 umask — 새 파일/디렉토리 기본 권한

```bash
umask         # 0022
umask 077     # 매우 엄격 (rwx------ for 자기, 나머지 없음)
umask 022     # 기본 일반 (755 dir, 644 file)
```

`umask` 는 권한에서 **빼는** 비트.

기본값:
- 파일: 666 - umask
- 디렉토리: 777 - umask

| umask | 새 파일 | 새 디렉토리 |
|-------|---------|-------------|
| 022 | 644 | 755 |
| 077 | 600 | 700 |
| 002 | 664 | 775 |

영구 설정:

```bash
# ~/.bashrc 또는 ~/.profile 또는 /etc/profile
umask 027    # 다른 사용자에게 r 도 안 줌
```

## 37.5 setuid / setgid / sticky

```
suid:  4000  실행 시 소유자 권한으로
sgid:  2000  실행 시 그룹 권한으로 / 디렉토리에서는 새 파일이 디렉토리 그룹 상속
sticky: 1000 디렉토리에서 자기 파일만 삭제 가능 (e.g. /tmp)
```

```bash
chmod 4755 program          # setuid
chmod 2755 dir              # setgid (디렉토리)
chmod 1777 shared_tmp       # sticky

# 심볼릭
chmod u+s program           # setuid
chmod g+s dir               # setgid
chmod +t shared_tmp         # sticky
```

`ls -l`:

```
-rwsr-xr-x   ← s = setuid (있는 곳이 x 면 s, 없으면 S)
drwxr-sr-x
drwxrwxrwt   ← t = sticky
```

### 보안 주의

setuid root 프로그램은 큰 공격 면 → 최소화.

```bash
# 모든 setuid 파일 점검
sudo find / -perm -4000 -type f 2>/dev/null
sudo find / -perm -2000 -type f 2>/dev/null
```

## 37.6 디렉토리 트리 권한 일괄

```bash
# 디렉토리 755, 파일 644
find /var/www -type d -exec chmod 755 {} +
find /var/www -type f -exec chmod 644 {} +

# 또는 X 활용
chmod -R u+rwX,go+rX,go-w /var/www

# 소유자 일괄
sudo chown -R www-data:www-data /var/www
```

## 37.7 권한 사고 회복

### 흔한 실수와 정상화

```bash
# 1. 홈 디렉토리 권한 망가짐
chmod 700 ~
chmod 700 ~/.ssh
chmod 600 ~/.ssh/id_*
chmod 644 ~/.ssh/*.pub
chmod 600 ~/.ssh/authorized_keys
chmod 600 ~/.ssh/known_hosts

# 2. /etc/sudoers 권한 (440)
sudo chmod 440 /etc/sudoers

# 3. /tmp sticky 손상
sudo chmod 1777 /tmp

# 4. 시스템 바이너리 권한
sudo chown root:root /bin/su
sudo chmod 4755 /bin/su

# 5. 패키지 표준 권한 복원 (debian)
sudo dpkg --verify
# RHEL
sudo rpm -Va | head
sudo rpm --setperms PACKAGE
sudo rpm --setugids PACKAGE
```

## 37.8 ACL 미리보기

기본 rwx 만으로 부족하면 ACL ([제38장]):

```bash
sudo apt install acl
getfacl file
setfacl -m u:bob:rw file
setfacl -d -m g:dev:rwX dir
```

## 37.9 capabilities — sudo 없이 특정 권한

```bash
sudo setcap cap_net_bind_service+ep /usr/bin/python3.11
# 1024 미만 포트 바인드 가능

getcap /usr/bin/python3.11

sudo setcap -r /usr/bin/python3.11   # 제거
```

흔한 capability:

| capability | 의미 |
|-----------|------|
| cap_net_bind_service | 1024 이하 포트 바인드 |
| cap_net_admin | 네트워크 설정 변경 |
| cap_net_raw | raw 소켓 (ping, tcpdump) |
| cap_sys_admin | 광범위 (위험) |
| cap_dac_override | 권한 검사 무시 |
| cap_setuid | UID 변경 |

## 37.10 자주 쓰는 한 줄

```bash
# 모든 .sh 실행 가능
find . -name '*.sh' -exec chmod +x {} +

# git 추적 파일 권한 정리
git ls-files -z | xargs -0 chmod 644

# 비밀파일 자동 600
chmod 600 ~/.aws/credentials ~/.netrc ~/.ssh/id_*

# 사용자 홈 권한 표준화
sudo find /home -mindepth 1 -maxdepth 1 -type d -exec sh -c '
  u=$(basename "$1")
  chown -R "$u":"$u" "$1"
  chmod 700 "$1"
' _ {} \;

# www 디렉토리 표준
sudo chown -R www-data:www-data /var/www
sudo find /var/www -type d -exec chmod 755 {} +
sudo find /var/www -type f -exec chmod 644 {} +

# setuid 파일 감사
sudo find / -perm -4000 -type f 2>/dev/null | tee setuid-list.txt

# world-writable 파일 점검
sudo find / -type f -perm -o=w 2>/dev/null

# 권한 8진수만 한 줄
stat -c '%a %n' file
```

## 37.11 함정

| 함정 | 대처 |
|------|------|
| `chmod -R 777 .` (절대 금지) | `find ... -type d/f` 분리 |
| 디렉토리 `r` 만 주고 `x` 없음 | 들어갈 수 없음. `x` 같이 |
| umask 가 777 → 새 파일 0 | 늘 022 또는 027 |
| ssh 키 권한 느슨 → 거절 | 600 |
| `~/.ssh` 권한 700 | |
| 새 파일 그룹이 의도와 다름 | 디렉토리 setgid (`g+s`) |
| `chown` 후에도 적용 안 됨 | 캐시 확인, NFS는 idmapd |
| 윈도우/네트워크 마운트의 권한 무시 | mount 옵션 (uid, gid, fmask, dmask) |

다음 챕터: [제38장]

\newpage

---


# 38. POSIX ACL — setfacl, getfacl

> 기본 rwx 가 부족할 때. "세 명의 다른 사용자에게 다른 권한"을 직접.

## 38.1 ACL 이 필요한 이유

전통 권한은 **소유자, 그룹, 기타** 셋만. 이걸로:

- "alice 와 bob 만 쓰기"
- "dev 그룹은 rw, ops 그룹은 r"
- "디렉토리 안 새 파일은 자동으로 X 그룹"

같은 요구를 표현 못 함. ACL 로 해결.

## 38.2 설치 / 활성

```bash
sudo apt install acl
sudo dnf install acl
```

대부분 ext4 / xfs / btrfs 가 ACL 기본 지원. 마운트 옵션:

```bash
mount | grep ' / '
# /dev/sda1 on / type ext4 (rw,relatime)

# 필요 시
sudo mount -o remount,acl /
# /etc/fstab 에 acl 옵션
```

## 38.3 getfacl — ACL 보기

```bash
getfacl file
# # file: file
# # owner: alice
# # group: dev
# user::rw-
# group::r--
# other::r--

getfacl -R dir/
getfacl --omit-header file        # 헤더 빼기
getfacl --absolute-names file     # 절대경로
```

## 38.4 setfacl — ACL 설정

### 사용자 / 그룹별 권한

```bash
setfacl -m u:bob:rw file               # bob 에게 rw
setfacl -m g:dev:rwx dir
setfacl -m o::r file                   # other
setfacl -m m::rx file                  # mask

setfacl -x u:bob file                  # 항목 제거
setfacl -b file                        # 모든 ACL 제거 (기본 rwx 만)
```

### 다중

```bash
setfacl -m u:alice:rw,u:bob:r,g:dev:rwx file
setfacl -m u:alice:rwx -R dir/
```

### 파일에서 일괄

```bash
getfacl src.txt > acls.txt
setfacl --restore=acls.txt
```

마이그레이션이나 백업 복원에 유용.

## 38.5 default ACL — 디렉토리 안 새 파일에 자동 적용

```bash
setfacl -d -m u:alice:rwx dir/
setfacl -d -m g:dev:rwx dir/
```

`-d` = default. 이후 dir 안에 만들어지는 새 파일/디렉토리가 자동으로 이 ACL 을 상속.

기존 파일에는 영향 없음. 한 번에 정리하려면:

```bash
setfacl -R -m u:alice:rwX dir/        # 기존 파일들에도 적용
setfacl -R -d -m u:alice:rwX dir/     # 새 파일에도
```

## 38.6 마스크 (effective)

ACL 마스크는 그룹/명명된 사용자/명명된 그룹의 **유효 최대 권한**.

```
user::rwx
user:alice:rwx          #effective:rw-
group::rwx              #effective:rw-
mask::rw-
other::r--
```

`alice` 가 rwx 받았어도 mask 가 rw 면 실효 권한은 rw.

```bash
setfacl -m m::rwx file       # 마스크 갱신
```

자주 쓰진 않지만, ACL 권한이 의도대로 안 먹을 때 항상 마스크부터 의심.

## 38.7 자주 쓰는 시나리오

### 공유 작업 디렉토리

`/srv/share` — dev 그룹은 rw, ops 그룹은 r, 새 파일도 동일.

```bash
sudo mkdir /srv/share
sudo chown root:dev /srv/share
sudo chmod 2775 /srv/share              # setgid (그룹 상속)
sudo setfacl -m g:dev:rwx,g:ops:rx /srv/share
sudo setfacl -d -m g:dev:rwX,g:ops:rX,o::- /srv/share
```

이제 dev 가 만든 파일은 자동으로 그룹=dev, ops 는 읽기만.

### 빌드 산출물 보호

```bash
setfacl -R -m u:ci:rwX,u:reader:rX,o::- /var/build
setfacl -R -d -m u:ci:rwX,u:reader:rX,o::- /var/build
```

### 임시 공유 (한 명에게만 더 권한)

```bash
setfacl -m u:bob:rw secret.csv
# 유효: 자기 600 + bob rw
ls -l secret.csv      # → -rw-rw----+ ('+' = ACL)
```

`+` 가 붙은 게 ACL 활성 표시.

## 38.8 ACL 백업 / 복원

```bash
# 현재 트리의 ACL 백업
getfacl -R /srv/share > /backup/share.acl

# 복원 (트리 구조가 같은 곳에서)
setfacl --restore=/backup/share.acl
```

`tar` / `rsync` 의 `-A`(rsync), `--acls`(tar) 옵션으로 메타와 같이 보존.

```bash
sudo tar --xattrs --acls -czpf data.tgz /srv/data
sudo tar --xattrs --acls -xzpf data.tgz -C /
rsync -avA src/ dst/
```

## 38.9 흔한 함정

| 함정 | 대처 |
|------|------|
| ACL 적용했는데 권한 안 들어감 | mask 확인, `-m m::rwx` |
| 새 파일에 ACL 안 붙음 | `-d` (default) 누락 |
| 백업/복원 후 사라짐 | `tar --acls`, `rsync -A`, getfacl/restore |
| 마운트 옵션에 acl 빠짐 | fstab 에 `acl` |
| nfs 에서 ACL 동작 이상 | NFSv4 ACL은 다른 모델, idmap 설정 |
| `+` 표시 후에도 권한 이상 | mask 점검 |
| 컨테이너 마운트에서 무시 | bind 마운트 옵션, overlay 한계 |

## 38.10 자주 쓰는 한 줄

```bash
# 빠른 확인
ls -l file       # '+' 면 ACL 활성
getfacl file

# 모든 ACL 제거 (기본 rwx 만)
setfacl -bR dir/

# 사용자 추가, 다른 사용자는 차단
chmod 700 secret/
setfacl -m u:bob:rwx secret/
setfacl -d -m u:bob:rwX secret/

# 그룹 협업 디렉토리
GRP=dev
sudo install -d -o root -g "$GRP" -m 2770 /srv/work
sudo setfacl -d -m g:"$GRP":rwX,o::- /srv/work

# ACL 만 차이 비교
diff <(getfacl -R --omit-header old/) <(getfacl -R --omit-header new/)

# tar 백업 (ACL 포함)
sudo tar --acls --xattrs -czpf etc.tgz /etc

# rsync 동기 (ACL 포함)
rsync -aAX src/ dst/      # -A=ACL, -X=xattr
```

다음 챕터: [제39장]

\newpage

---


# 39. sudo, su, doas — 권한 상승

> 한 줄만 root, 그 외엔 일반 사용자. 안전과 편의의 균형.

## 39.1 su 와 sudo 의 차이

| 도구 | 인증 | 권한 |
|------|------|------|
| `su` | 대상 사용자의 패스워드 | 그 사용자로 전환 |
| `sudo` | 본인의 패스워드 | sudoers 룰에 따라 |
| `su -` | 대상 패스워드 | 환경/PWD 까지 그 사용자처럼 |
| `doas` | 본인 (단순) | OpenBSD 스타일 |

대부분의 운영 환경은 `sudo`. `su` 는 거의 안 쓰임.

## 39.2 sudo 기본

```bash
sudo cmd                    # root 로 실행
sudo -u alice cmd           # alice 로
sudo -i                     # root 로 로그인 셸
sudo -s                     # root 셸 (현재 환경)
sudo -k                     # 캐시된 인증 삭제
sudo -v                     # 인증만 갱신
sudo -l                     # 내 sudo 권한 목록
sudo -ll                    # 자세히
sudo -E cmd                 # 환경변수 보존 (제한 있음)
sudo -H cmd                 # HOME 을 root 의 것으로
```

### 패스워드 캐싱

기본 5분간 재인증 안 함 (sudoers `timestamp_timeout`).

```bash
sudo -v          # 캐시 갱신
sudo -k          # 캐시 무효화
sudo -K          # 영구 (재부팅 후도)
```

## 39.3 sudoers 파일 — visudo

**반드시 visudo 로**. 문법 오류로 sudo 자체가 잠기는 사고 방지.

```bash
sudo visudo                                # 기본 /etc/sudoers
sudo visudo -f /etc/sudoers.d/myrules      # 분할 파일
```

### 핵심 룰 형식

```
USER  HOSTS = (RUNAS:GROUPS)  TAGS:  COMMANDS
```

예:

```
root    ALL=(ALL:ALL) ALL
%sudo   ALL=(ALL:ALL) ALL
%wheel  ALL=(ALL) ALL
alice   ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart nginx
deploy  prod  =(www-data) /usr/bin/git, /usr/bin/rsync
```

| 필드 | 의미 |
|------|------|
| USER | 사용자 또는 `%group` 또는 `+netgroup` 또는 `User_Alias` |
| HOSTS | 어디서 실행 가능 (보통 `ALL`) |
| `(RUNAS:GROUPS)` | 어떤 사용자/그룹으로 실행 가능 |
| TAGS | `NOPASSWD:`, `PASSWD:`, `LOG_INPUT:`, `LOG_OUTPUT:`, `SETENV:` |
| COMMANDS | 절대경로 명령 목록, 또는 `ALL` |

### Alias

```
User_Alias  ADMINS = alice, bob
Cmnd_Alias  RESTART = /usr/bin/systemctl restart *, /usr/bin/systemctl reload *
Host_Alias  WEB = web1, web2, web3

ADMINS  WEB = NOPASSWD: RESTART
```

## 39.4 흔한 룰 패턴

### 그룹에 root 권한

```
%sudo   ALL=(ALL:ALL) ALL          # debian/ubuntu 기본
%wheel  ALL=(ALL) ALL              # rhel 전통
```

```bash
sudo usermod -aG sudo alice        # debian
sudo usermod -aG wheel alice       # rhel
```

### 패스워드 없이 특정 명령만

```
deploy  ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart nginx, \
                            /usr/bin/systemctl reload nginx, \
                            /usr/sbin/nginx -t
```

CI / 배포 시스템 흔한 형태.

### 다른 사용자로 실행

```
seunghwa ALL=(www-data) NOPASSWD: /usr/local/bin/deploy.sh
```

```bash
sudo -u www-data /usr/local/bin/deploy.sh
```

### 환경 보존

기본은 `secure_path`, `env_reset` 으로 환경변수 거의 다 제거. 보존하려면:

```
Defaults  env_keep += "EDITOR PAGER LANG"
seunghwa ALL=(ALL) SETENV: ALL
```

## 39.5 sudoers 안전 옵션

```
Defaults  requiretty                       # tty 없으면 거절 (기본 OFF)
Defaults  !visiblepw                       # 패스워드 보이는 환경 차단
Defaults  always_set_home                  # 자동 -H
Defaults  match_group_by_gid               # 효율
Defaults  always_query_group_plugin        # ldap 그룹 호환
Defaults  passwd_tries=3                   # 패스워드 시도 횟수
Defaults  passwd_timeout=1                 # 분
Defaults  timestamp_timeout=5              # 캐시 분
Defaults  badpass_message="Wrong"
Defaults  insults                          # 잘못 입력 시 농담 (재미)
Defaults  log_input,log_output             # 모든 입출력 기록
Defaults  iolog_dir="/var/log/sudo-io"
Defaults  lecture=once
Defaults  use_pty                          # PTY 강제
```

## 39.6 sudo 로깅

기본 로그:

```bash
sudo grep sudo /var/log/auth.log
sudo journalctl -t sudo --since today
```

로그 입출력 (보안 감사):

```
Defaults log_input,log_output
Defaults iolog_dir=/var/log/sudo-io
```

`sudoreplay` 로 재생:

```bash
sudoreplay -l
sudoreplay -d /var/log/sudo-io ID
```

## 39.7 su

```bash
su                  # root (root 패스워드 필요)
su -                # 환경/PWD 까지 root
su alice            # alice 로
su - alice          # alice 환경까지
su -c 'cmd' alice   # 명령 한 번
```

대부분 시스템에서 root 패스워드는 잠겨 있어 `su` 자체가 안 된다 (Ubuntu). `sudo -i` 가 보통.

## 39.8 doas — sudo의 단순한 대안

OpenBSD 출신. 리눅스 포팅판:

```bash
sudo apt install doas

# /etc/doas.conf
permit persist :wheel
permit nopass alice cmd /usr/bin/systemctl
```

```bash
doas vi /etc/hosts
doas -u www-data /usr/local/bin/deploy.sh
```

설정이 짧고 로깅도 단순. 작은 시스템에 좋음.

## 39.9 sudo 사용 베스트 프랙티스

1. **항상 visudo 로 편집** — 문법 오류 방지
2. **분할 파일 사용** — `/etc/sudoers.d/00-deploy` 같이
3. **NOPASSWD 는 정확한 절대경로 명령으로 한정**
4. **`ALL` 와일드카드 신중히** — 셸 메타로 escape 가능
5. **인자 검사** — `systemctl restart *` 는 의도 외 인자 가능
6. **로깅 활성화** — 운영 시스템은 log_input/output
7. **그룹 사용** — 개인 룰 대신 `%admins`, `%deploy`
8. **승격 후 셸 권한 최소화** — 한 줄만 sudo, 그 외 일반 사용자
9. **에디터는 sudoedit** — 임시 복사 + 권한 안전

```bash
sudoedit /etc/nginx/nginx.conf
# 또는
sudo -e /etc/nginx/nginx.conf
```

`sudoedit` 는 root 권한으로 임시 복사 → 사용자가 자기 에디터로 편집 → 저장 시 root 가 다시 쓰는 패턴. ROOT 셸 노출 없음.

## 39.10 함정과 보안

| 함정 | 대처 |
|------|------|
| sudoers 직접 편집 후 재로드 X | `visudo` (문법 검증) |
| `NOPASSWD: /usr/bin/find` | find -exec 로 root 셸 가능. 위험 |
| `NOPASSWD: /bin/chmod` | 시스템 권한 통째 변경 가능 |
| 와일드카드 `*` 인자 | 셸 확장 후 의도 외 인자 |
| 환경변수 PATH | `secure_path` 의 PATH 만 |
| `/etc/sudoers.d/*` 권한 | 0440 |
| TTY 없이 쓸 때 막힘 | `requiretty` 끔 (자동화) 또는 `-t` |
| `sudo cmd > /etc/x` | sudo 가 cmd 만, `>` 는 셸 → `sudo tee` 사용 |

리스크 큰 NOPASSWD 룰 예:

```
# 절대 X
deploy ALL=(ALL) NOPASSWD: /bin/sh
deploy ALL=(ALL) NOPASSWD: /usr/bin/vi
deploy ALL=(ALL) NOPASSWD: /usr/bin/find
deploy ALL=(ALL) NOPASSWD: /usr/bin/awk
# 이 모두 root 셸로 escape 가능
```

좁은 범위로:

```
deploy ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart nginx.service
```

## 39.11 자주 쓰는 한 줄

```bash
# 내가 어떤 sudo 권한 가졌나
sudo -l

# root 셸로 (환경 깨끗)
sudo -i

# 다른 사용자로 임시
sudo -u www-data -H bash

# 로그 본 사람
sudo last
sudo journalctl -t sudo --since today

# 분할 파일 작성 (안전)
sudo install -m 0440 -o root -g root /dev/stdin /etc/sudoers.d/deploy <<'EOF'
deploy ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart nginx.service
EOF
sudo visudo -c    # 검증

# 실수로 sudoers 깨졌을 때
pkexec visudo                       # polkit
# 또는 단일 사용자 모드 부팅 → root 권한
```

다음 챕터: [제40장]

\newpage

---


# 40. openssl — 인증서 / 암호화 / 해시

> TLS 도구이자 만능 암호화 칼.

## 40.1 빠른 사용 모음

```bash
# 임의 패스워드
openssl rand -base64 24

# 임의 16진
openssl rand -hex 32

# 해시
echo -n "hello" | openssl dgst -sha256
openssl dgst -sha256 file
openssl sha256 file

# Base64
echo "hello" | openssl base64
echo "aGVsbG8K" | openssl base64 -d
```

## 40.2 키 / 인증서 (TLS 위주)

### RSA 키

```bash
# 새 RSA 개인키
openssl genrsa -out key.pem 4096

# 패스프레이즈 보호 키
openssl genrsa -aes256 -out key.pem 4096

# 패스프레이즈 제거
openssl rsa -in key.pem -out key.nopass.pem

# 공개키 추출
openssl rsa -in key.pem -pubout -out pub.pem
```

### EC (현대 권장)

```bash
openssl ecparam -name prime256v1 -genkey -noout -out key.pem
openssl ec -in key.pem -pubout -out pub.pem
```

### Ed25519

```bash
openssl genpkey -algorithm ED25519 -out key.pem
```

### CSR (Certificate Signing Request)

```bash
openssl req -new -key key.pem -out csr.pem \
  -subj "/CN=example.com/O=Acme/C=KR"

# 다중 SAN
openssl req -new -key key.pem -out csr.pem \
  -subj "/CN=example.com" \
  -addext "subjectAltName=DNS:example.com,DNS:www.example.com,IP:1.2.3.4"
```

### 자체 서명 인증서

```bash
openssl req -x509 -new -nodes -key key.pem -days 365 -out cert.pem \
  -subj "/CN=example.com" \
  -addext "subjectAltName=DNS:example.com,DNS:www.example.com"

# 한 번에 (key + cert)
openssl req -x509 -newkey rsa:4096 -nodes \
  -keyout key.pem -out cert.pem -days 365 \
  -subj "/CN=localhost" \
  -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"
```

`-nodes` (no des) = 패스프레이즈 없이.

### 인증서 보기

```bash
openssl x509 -in cert.pem -noout -text
openssl x509 -in cert.pem -noout -subject -issuer -dates -fingerprint
openssl x509 -in cert.pem -noout -ext subjectAltName
openssl x509 -in cert.pem -noout -serial
openssl x509 -in cert.pem -noout -pubkey
```

### 인증서 검증

```bash
openssl verify -CAfile ca.pem cert.pem
openssl verify -CAfile ca.pem -untrusted intermediate.pem cert.pem

# 키와 인증서 짝 확인
openssl x509 -noout -modulus -in cert.pem | openssl md5
openssl rsa  -noout -modulus -in key.pem  | openssl md5
# 두 해시 같아야 함
```

## 40.3 PKCS / 변환

```bash
# PEM ↔ DER
openssl x509 -in cert.pem -outform DER -out cert.der
openssl x509 -in cert.der -inform DER -out cert.pem

# PEM → PFX (PKCS#12)
openssl pkcs12 -export -inkey key.pem -in cert.pem -certfile chain.pem \
  -out bundle.pfx -name "myserver"

# PFX → PEM
openssl pkcs12 -in bundle.pfx -out bundle.pem -nodes
openssl pkcs12 -in bundle.pfx -nocerts -out key.pem -nodes
openssl pkcs12 -in bundle.pfx -nokeys -clcerts -out cert.pem

# PKCS#8 변환
openssl pkcs8 -topk8 -in key.pem -out key.pk8 -nocrypt
```

## 40.4 TLS 진단 — s_client / s_server

```bash
# 인증서 정보 + 핸드셰이크
openssl s_client -connect example.com:443 -servername example.com

# 종료까지
echo | openssl s_client -connect example.com:443 -servername example.com 2>/dev/null \
  | openssl x509 -noout -dates -subject -issuer

# 체인 전체
openssl s_client -showcerts -connect example.com:443 -servername example.com < /dev/null

# STARTTLS
openssl s_client -connect smtp:25 -starttls smtp
openssl s_client -connect imap:143 -starttls imap
openssl s_client -connect pop3:110 -starttls pop3
openssl s_client -connect xmpp:5222 -starttls xmpp

# TLS 버전 강제
openssl s_client -tls1_2 -connect host:443
openssl s_client -tls1_3 -connect host:443

# 사이퍼 강제
openssl s_client -cipher ECDHE-RSA-AES256-GCM-SHA384 -connect host:443
```

### 만료일 체크 (자동화)

```bash
END=$(echo | openssl s_client -connect example.com:443 -servername example.com 2>/dev/null \
  | openssl x509 -noout -enddate | cut -d= -f2)
echo "Expires: $END"
EXP=$(date -d "$END" +%s)
NOW=$(date +%s)
DAYS=$(( (EXP - NOW) / 86400 ))
echo "$DAYS days left"
```

### s_server (테스트용)

```bash
openssl s_server -cert cert.pem -key key.pem -accept 4433 -www
```

브라우저에서 `https://localhost:4433` 으로 테스트.

## 40.5 해시

```bash
openssl dgst -sha256 file
openssl dgst -sha512 file
openssl dgst -md5 file               # 무결성만, 보안 X
openssl sha256 *.pdf
openssl dgst -sha256 -hmac "secret" file
openssl dgst -sha256 -sign key.pem -out file.sig file
openssl dgst -sha256 -verify pub.pem -signature file.sig file
```

## 40.6 대칭 암호화 (enc)

```bash
# 암호화
openssl enc -aes-256-cbc -salt -pbkdf2 -in plain -out enc.bin

# 복호화
openssl enc -aes-256-cbc -d -pbkdf2 -in enc.bin -out plain

# 패스워드를 파일에서
openssl enc -aes-256-cbc -salt -pbkdf2 -pass file:./pw.txt \
  -in plain -out enc.bin

# 키 파일로 (운영용은 GPG 또는 age 권장)
openssl enc -aes-256-gcm -K $(openssl rand -hex 32) -iv $(openssl rand -hex 12) \
  -in plain -out enc.bin
```

`enc` 는 PBKDF2 옵션 안 주면 약하다. `-pbkdf2`+`-iter 100000` 권장. 운영 보안은 [age](https://age-encryption.org/) / GPG 가 더 안전.

## 40.7 Base64 / Hex / URL safe

```bash
echo "hello" | openssl base64
echo "aGVsbG8K" | openssl base64 -d

# URL safe (rfc4648 §5)
openssl rand 24 | basenc --base64url -

# Hex
echo "hello" | xxd -p
echo "68656c6c6f0a" | xxd -r -p
```

## 40.8 비대칭 암호화 / 서명

```bash
# 데이터 암호화 (키교환용; 큰 파일은 sym + 키 비대칭이 정석)
openssl rsautl -encrypt -pubin -inkey pub.pem -in plain -out enc.bin
openssl rsautl -decrypt -inkey key.pem -in enc.bin -out plain
# (rsautl 은 deprecated, openssl pkeyutl 권장)

openssl pkeyutl -encrypt -pubin -inkey pub.pem -in plain -out enc.bin
openssl pkeyutl -decrypt -inkey key.pem -in enc.bin -out plain

# 서명/검증
openssl pkeyutl -sign -inkey key.pem -in hash.bin -out sig.bin
openssl pkeyutl -verify -pubin -inkey pub.pem -sigfile sig.bin -in hash.bin
```

## 40.9 CA 운영 (작은 사설 CA)

```bash
# 1. CA 키 + 인증서
openssl genrsa -aes256 -out ca.key 4096
openssl req -x509 -new -key ca.key -days 3650 -out ca.crt \
  -subj "/CN=My Internal CA/O=Acme/C=KR"

# 2. 서버 키 + CSR
openssl genrsa -out server.key 4096
openssl req -new -key server.key -out server.csr \
  -subj "/CN=app.internal" \
  -addext "subjectAltName=DNS:app.internal,DNS:app"

# 3. CA 가 서명
openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial \
  -out server.crt -days 365 \
  -extfile <(printf "subjectAltName=DNS:app.internal,DNS:app")

# 4. 클라이언트가 신뢰하도록 ca.crt 배포
sudo cp ca.crt /usr/local/share/ca-certificates/my-ca.crt
sudo update-ca-certificates              # debian
sudo trust anchor ca.crt                  # rhel
```

## 40.10 자주 쓰는 한 줄

```bash
# HTTPS 인증서 만료일
openssl s_client -connect example.com:443 -servername example.com </dev/null 2>/dev/null \
  | openssl x509 -noout -enddate

# 서버 인증서 체인 저장
openssl s_client -showcerts -connect example.com:443 -servername example.com </dev/null 2>/dev/null \
  | sed -n '/-----BEGIN/,/-----END/p' > chain.pem

# 인증서 호환성 진단 (지원 사이퍼)
nmap --script ssl-enum-ciphers -p 443 example.com

# 자체 서명 빠른 발급 (개발용)
openssl req -x509 -newkey rsa:2048 -nodes -days 365 \
  -subj "/CN=localhost" -addext "subjectAltName=DNS:localhost,IP:127.0.0.1" \
  -keyout key.pem -out cert.pem

# 패스워드 해시 (crypt(3))
openssl passwd -6 'mypass'        # SHA-512 (linux 표준)
openssl passwd -1 'mypass'        # MD5

# 임의 토큰
openssl rand -hex 32
openssl rand -base64 32
openssl rand 32 | base64

# JWT 서명 (간단)
HEADER=$(echo -n '{"alg":"HS256","typ":"JWT"}' | openssl base64 -A | tr '+/' '-_' | tr -d '=')
PAYLOAD=$(echo -n '{"sub":"alice"}' | openssl base64 -A | tr '+/' '-_' | tr -d '=')
SIG=$(echo -n "$HEADER.$PAYLOAD" | openssl dgst -sha256 -hmac "secret" -binary | openssl base64 -A | tr '+/' '-_' | tr -d '=')
echo "$HEADER.$PAYLOAD.$SIG"

# CRL 보기
openssl crl -in crl.pem -noout -text
```

## 40.11 함정

| 함정 | 대처 |
|------|------|
| `enc` 가 약한 KDF 사용 | `-pbkdf2 -iter 100000` |
| 키와 인증서 짝 안 맞음 | modulus md5 비교 |
| SAN 누락 → 브라우저 경고 | `subjectAltName` 항상 포함 |
| 체인 빠뜨림 | 서버에 cert+intermediate 모두 |
| openssl 1.0 vs 1.1 vs 3 옵션 차이 | 버전별 매뉴얼 |
| 시스템 시계 어긋나면 검증 실패 | NTP |
| HSTS 가 자체서명 막음 | 인증서 신뢰 등록 또는 다른 호스트명 |

다음 챕터: [제41장]

\newpage

---


# 41. df, du, mount, lsblk — 디스크와 마운트

> 디스크가 얼마나 남았나, 무엇이 어디에 마운트됐나.

## 41.1 df — 파일시스템 사용량

```bash
df                    # 1KB 블록
df -h                 # human (MB/GB)
df -H                 # human (1000 단위, SI)
df -T                 # 파일시스템 타입
df -i                 # inode 사용량
df -h /var
df -h --output=source,size,used,avail,pcent,target
df -x tmpfs -x devtmpfs -h    # 일부 타입 제외
df -h --total
```

```
Filesystem      Size  Used Avail Use% Mounted on
/dev/sda1       100G   50G   50G  50% /
tmpfs           4.0G   10M  4.0G   1% /run
```

`Use% 100%` 인데 `df -i` 도 100% 가까우면 inode 고갈, 아니면 디스크 공간.

## 41.2 du — 디렉토리 사용량

```bash
du -sh dir/              # 합계
du -sh *
du -sh * 2>/dev/null | sort -h
du -h --max-depth=1 .
du -h --max-depth=2 / 2>/dev/null | sort -h | tail -20
du -hs --time dir/         # 마지막 수정 시각

# 특정 파일시스템만 (mount 경계 안 넘음)
du -shx /var/

# 큰 파일/디렉토리 톱
du -ah . 2>/dev/null | sort -h | tail
```

| 옵션 | 의미 |
|------|------|
| `-s` | 합계만 |
| `-h` | human |
| `-c` | 총합 추가 |
| `-d N` 또는 `--max-depth=N` | 깊이 |
| `-x` | 다른 파일시스템 안 넘음 |
| `-a` | 모든 파일 |
| `-L` | 심볼릭 따라감 |
| `--apparent-size` | 논리 크기 (sparse 정직) |
| `-t SIZE` | SIZE 보다 큰 것만 (`-t 100M`) |
| `--time` | mtime |

### du 와 ls -l 차이

`ls -l` 는 파일 크기 (논리). `du` 는 블록 사용량 (디스크 실제). 작은 파일이 많으면 du > ls 합계.

## 41.3 ncdu — 인터랙티브 디스크 사용량

```bash
sudo apt install ncdu
ncdu /
ncdu -x /             # 마운트 경계 무시
ncdu -o report.json /
ncdu -f report.json   # 결과 다시 보기
```

`d` 로 삭제, `n/s` 정렬 토글. 큰 디렉토리 정리 1순위.

## 41.4 lsblk — 블록 디바이스 트리

```bash
lsblk
lsblk -f                # 파일시스템/UUID
lsblk -o NAME,SIZE,TYPE,FSTYPE,UUID,MOUNTPOINT
lsblk -d                # 디스크만
lsblk -p                # 풀 경로
lsblk -J                # JSON
```

```
NAME   MAJ:MIN RM  SIZE RO TYPE MOUNTPOINTS
sda      8:0    0  500G  0 disk
├─sda1   8:1    0    1G  0 part /boot
├─sda2   8:2    0  100G  0 part /
└─sda3   8:3    0  399G  0 part /home
```

### blkid

```bash
sudo blkid
sudo blkid /dev/sda1
sudo blkid -o value -s UUID /dev/sda1
```

## 41.5 mount / umount

```bash
mount                                        # 모든 마운트 (또는 cat /proc/mounts)
mount | column -t

sudo mount /dev/sdb1 /mnt/usb
sudo mount -t ext4 -o ro,noatime /dev/sdb1 /mnt/usb
sudo mount UUID=... /mnt/data
sudo mount LABEL=mylabel /mnt/data
sudo mount -a                                # /etc/fstab 모두

sudo umount /mnt/usb
sudo umount /dev/sdb1
sudo umount -l /mnt/usb                      # lazy (사용 중이어도)
sudo umount -f /mnt/usb                      # 강제 (NFS 류)
```

### 자주 쓰는 옵션

| 옵션 | 의미 |
|------|------|
| `ro` / `rw` | 읽기/읽기쓰기 |
| `noatime` | atime 안 갱신 (성능) |
| `relatime` | 일부만 갱신 (기본) |
| `nodiratime` | 디렉토리 atime 안 |
| `noexec` | 실행 금지 |
| `nosuid` | setuid 무시 |
| `nodev` | 디바이스 노드 무시 |
| `user` | 일반 사용자 마운트 가능 |
| `users` | 누구나 umount 가능 |
| `defaults` | rw,suid,dev,exec,auto,nouser,async |
| `bind` | 디렉토리를 다른 곳에 |
| `loop` | 파일을 디바이스처럼 |
| `remount` | 옵션 변경하며 재마운트 |
| `acl` | ACL 활성 |
| `discard` | TRIM (SSD) |
| `errors=remount-ro` | ext4 에러 시 RO |

### bind 마운트

```bash
sudo mount --bind /var/log /mnt/logs        # 같은 데이터, 다른 위치
sudo mount --rbind /              /mnt/root # 재귀 (서브 마운트도)
sudo mount --make-private /mnt/root         # 공유 정책 변경
```

### loop 마운트 (파일을 디스크처럼)

```bash
sudo mount -o loop ubuntu.iso /mnt/iso
sudo umount /mnt/iso

# 가상 디스크 만들기
dd if=/dev/zero of=disk.img bs=1M count=100
mkfs.ext4 disk.img
sudo mount -o loop disk.img /mnt/img
```

### remount

```bash
sudo mount -o remount,ro /mnt/data         # 읽기 전용으로
sudo mount -o remount,rw /mnt/data
sudo mount -o remount /                    # 옵션 그대로
```

## 41.6 /etc/fstab — 영구 마운트

```
# <device>            <mount>      <type>  <options>           <dump>  <pass>
UUID=abcd-1234        /            ext4    defaults,noatime    0       1
UUID=efgh-5678        /home        ext4    defaults,noatime    0       2
LABEL=swap            none         swap    sw                  0       0
/srv/data.img         /mnt/data    ext4    loop,noatime        0       0
nfs.example.com:/srv  /mnt/nfs     nfs     defaults,_netdev    0       0
//server/share        /mnt/cifs    cifs    credentials=/etc/cifs.cred,_netdev,uid=1000  0  0
192.168.1.10:/data    /mnt/nfs     nfs4    rw,_netdev          0       0
```

| 필드 | 의미 |
|------|------|
| device | 디바이스/UUID/LABEL/원격 |
| mount | 마운트 포인트 |
| type | 파일시스템 |
| options | 마운트 옵션 |
| dump | dump 백업 (0 보통) |
| pass | fsck 순서 (0=안 함, 1=루트, 2=나머지) |

검증:

```bash
sudo mount -a              # fstab 모두 마운트 (실수 발견)
findmnt --verify           # fstab 검증
```

`_netdev` — 네트워크 마운트는 네트워크 준비 후.

## 41.7 swap

```bash
sudo swapon --show
sudo free -h
sudo swapon /swap.img
sudo swapoff /swap.img

# swap 파일 만들기
sudo fallocate -l 2G /swap.img
sudo chmod 600 /swap.img
sudo mkswap /swap.img
sudo swapon /swap.img
echo '/swap.img none swap sw 0 0' | sudo tee -a /etc/fstab
```

## 41.8 fsck — 파일시스템 검사

```bash
sudo umount /dev/sdb1
sudo fsck -y /dev/sdb1            # ext 자동 yes
sudo fsck.ext4 -f /dev/sdb1
sudo xfs_repair /dev/sdb1         # xfs (마운트 해제 필수)

# 다음 부팅 시 검사
sudo touch /forcefsck
```

마운트된 ext 에는 절대 수동 fsck 금지.

## 41.9 디스크 공간 부족 진단

```bash
# 1. df 확인
df -h
df -i

# 2. 큰 디렉토리
sudo du -shx /* 2>/dev/null | sort -h | tail

# 3. 큰 파일
sudo find / -xdev -type f -size +1G 2>/dev/null

# 4. 삭제됐지만 열려 있는
sudo lsof +L1 | head

# 5. journal 정리
sudo journalctl --vacuum-time=7d

# 6. 패키지 캐시
sudo apt clean
sudo dnf clean all

# 7. 도커
docker system df
docker system prune -af

# 8. 휴지통 / 임시
rm -rf ~/.cache/*
sudo rm -rf /tmp/*       # 조심
```

## 41.10 자주 쓰는 한 줄

```bash
# 마운트 깔끔히
findmnt -t ext4,xfs

# UUID 로 fstab 만들기
echo "UUID=$(sudo blkid -s UUID -o value /dev/sdb1) /mnt/data ext4 defaults,noatime 0 2" \
  | sudo tee -a /etc/fstab

# /home 큰 사용자 톱
sudo du -shx /home/* 2>/dev/null | sort -h | tail

# 변화량 (10초 사이)
df --output=avail -B1 / | tail -1
sleep 10
df --output=avail -B1 / | tail -1
# 차이 = 변화

# 큰 로그 정리
sudo journalctl --vacuum-size=200M
sudo find /var/log -type f -size +100M -mtime +30 -print -delete

# 디스크 IO 톱
sudo iotop
sudo iostat -x 1

# nvme/SMART
sudo smartctl -a /dev/sda
sudo smartctl -t short /dev/sda
```

## 41.11 함정

| 함정 | 대처 |
|------|------|
| 마운트 포인트가 비어있지 않음 | 빈 디렉토리에 마운트 권장 |
| umount busy | `lsof +D /mount`, `fuser -m`, `-l` lazy |
| /etc/fstab 오타 → 부팅 실패 | `mount -a` 로 검증, `findmnt --verify` |
| 디스크는 남는데 inode 고갈 | `df -i`, 작은 파일 정리 |
| `du` vs `df` 차이 | 삭제됐지만 열린 파일 (`lsof +L1`) |
| 네트워크 마운트가 부팅 차단 | `_netdev`, `nofail` |
| SSD trim 안 됨 | `discard` 옵션 또는 `fstrim.timer` |
| `noexec` 인 곳에서 실행 안 됨 | `mount -o remount,exec` |

다음 챕터: [제42장]

\newpage

---


# 42. dd — 블록 단위 복사 / 디스크 이미지

> "disk destroyer" 별명을 얻은 이유. 블록을 정확히 옮기지만 한 번 실수면 끝.

## 42.1 기본 형식

```
dd if=INPUT of=OUTPUT bs=BLOCK count=N
```

| 인자 | 의미 |
|------|------|
| `if=` | input file (기본 stdin) |
| `of=` | output file (기본 stdout) |
| `bs=` | block size (`bs=1M`, `bs=4096`) |
| `ibs=`, `obs=` | 입/출 블록 따로 |
| `count=` | 복사할 블록 수 |
| `skip=` | 입력에서 N 블록 건너뜀 |
| `seek=` | 출력에서 N 블록 위치로 점프 |
| `conv=` | 변환 (notrunc, noerror, sync, fdatasync, ...) |
| `iflag=`, `oflag=` | 플래그 (direct, dsync, ...) |
| `status=progress` | 진행 표시 (GNU coreutils 8.24+) |

## 42.2 자주 쓰는 패턴

### USB / SD 카드 이미지 굽기

```bash
# 디바이스 확인 (절대 정확히!)
lsblk

# 굽기 (예: /dev/sdb)
sudo dd if=ubuntu.iso of=/dev/sdb bs=4M status=progress oflag=direct conv=fdatasync
```

`oflag=direct` — 페이지 캐시 우회로 빠름. `conv=fdatasync` — 마지막에 sync 보장.

> **경고**: `of=` 를 잘못 적으면 시스템 디스크가 박살난다. 항상 `lsblk` 로 정확히 확인.

### 디스크 → 이미지

```bash
# 미사용 디스크의 이미지 통째 떠두기
sudo dd if=/dev/sdb of=usb.img bs=4M status=progress conv=sync,noerror

# 압축 동시에
sudo dd if=/dev/sdb bs=4M status=progress | gzip > usb.img.gz

# 풀기
gunzip -c usb.img.gz | sudo dd of=/dev/sdb bs=4M status=progress
```

### 이미지 → 디스크

```bash
sudo dd if=usb.img of=/dev/sdb bs=4M status=progress oflag=direct conv=fdatasync
```

### 파티션 이미지

```bash
sudo dd if=/dev/sdb1 of=part.img bs=4M status=progress
```

### MBR / 부트섹터

```bash
# MBR 백업 (첫 512 바이트)
sudo dd if=/dev/sda of=mbr.bin bs=512 count=1

# MBR 복원
sudo dd if=mbr.bin of=/dev/sda bs=512 count=1

# 부트로더만 (파티션 테이블 보존)
sudo dd if=mbr.bin of=/dev/sda bs=446 count=1
```

### 디스크 와이프 (정확하지만 느림)

```bash
# 0 으로
sudo dd if=/dev/zero of=/dev/sdb bs=4M status=progress

# 임의값으로 (보안 와이프)
sudo dd if=/dev/urandom of=/dev/sdb bs=4M status=progress

# 빠른 와이프 (첫 100MB만 — 부트/파티션테이블)
sudo dd if=/dev/zero of=/dev/sdb bs=1M count=100
```

> SSD 는 dd 와이프보다 `blkdiscard` / 제조사 secure erase 가 효과적.

```bash
sudo blkdiscard -v /dev/nvme0n1
```

### 가상 디스크 만들기

```bash
# 1 GiB sparse 파일
dd if=/dev/zero of=disk.img bs=1M count=0 seek=1024
# → 즉시 1G 처럼 보이지만 실제 디스크 0 (sparse)

# 진짜 1 GiB
dd if=/dev/zero of=disk.img bs=1M count=1024 status=progress
# 또는
fallocate -l 1G disk.img    # 더 빠름
```

마운트:

```bash
mkfs.ext4 disk.img
sudo mount -o loop disk.img /mnt/img
```

### 전송 속도 측정

```bash
dd if=/dev/zero of=/tmp/testfile bs=1M count=1000 conv=fdatasync
# 시간 + 속도 출력
```

## 42.3 진행 / 중단

```bash
# 진행 표시
sudo dd if=... of=... status=progress

# 진행 표시 없이 진행 보고 싶을 때 (옛날 dd)
# 다른 셸에서:
sudo kill -USR1 $(pidof dd)

# 또는 watch
watch -n 1 'sudo kill -USR1 $(pidof dd) 2>/dev/null'
```

`status=progress` 가 가장 편리.

## 42.4 정확한 길이

```bash
# 첫 1GB 만 복사
dd if=in of=out bs=1M count=1024

# 100MB 위치부터 50MB 복사
dd if=in of=out bs=1M skip=100 count=50

# 출력 파일 안 자르기 (공간 일부만 갱신)
dd if=patch.bin of=disk.img bs=512 seek=2048 count=1 conv=notrunc
```

`conv=notrunc` 빠뜨리면 출력 파일이 그 길이로 잘릴 수 있음. 부분 갱신 시 필수.

## 42.5 conv / iflag / oflag

| conv | 의미 |
|------|------|
| `notrunc` | 출력 자르지 않음 |
| `noerror` | 읽기 에러 무시 (계속) |
| `sync` | 부족한 블록을 0 으로 채움 |
| `fdatasync` | 마지막에 fdatasync |
| `fsync` | fsync |
| `swab` | 바이트 swap |
| `lcase` / `ucase` | 대/소문자 변환 (옛날) |

| iflag/oflag | 의미 |
|-------------|------|
| `direct` | O_DIRECT (페이지 캐시 우회) |
| `dsync` | 매 블록 dsync |
| `sync` | 매 블록 sync |
| `nonblock` | non-blocking |
| `fullblock` | 입력을 꽉 채울 때까지 |

복구용 권장:

```bash
sudo dd if=/dev/sdc of=image.bin bs=64K conv=noerror,sync status=progress
# 읽기 에러 나도 0 으로 채워 계속 → 손상된 디스크라도 가능한 한 회수
```

`ddrescue` 가 손상 디스크 복구에 더 적합:

```bash
sudo apt install gddrescue
sudo ddrescue -d -r 3 /dev/sdc image.bin map.log
```

## 42.6 dd 의 단위

```
1   = 1 byte
512 = 1 sector
1K  = 1024
1M  = 1024K
1G  = 1024M
kB, MB, GB = 1000 단위 (작은 b)
```

`bs=1M count=10` = 10 MiB.

## 42.7 자주 쓰는 한 줄

```bash
# USB 굽기 (status=progress 필수)
sudo dd if=ubuntu-22.04.iso of=/dev/sdb bs=4M status=progress oflag=direct conv=fdatasync

# 파일 뒷부분만
dd if=big.bin bs=1M skip=100 of=tail.bin

# 파일 일부 추출
dd if=disk.img bs=1 skip=$OFFSET count=$LEN of=out.bin

# zero / random 1M 파일
dd if=/dev/zero of=zero.bin bs=1M count=1
dd if=/dev/urandom of=rand.bin bs=1M count=1

# 아주 빠른 sparse 큰 파일
truncate -s 10G big.img            # 또는 fallocate
# (dd 보다 즉시)

# 파일 끝 마지막 1KB
dd if=file bs=1 skip=$(( $(stat -c%s file) - 1024 )) count=1024 of=tail.bin

# 디스크 서명 확인 (첫 16바이트)
sudo dd if=/dev/sda bs=16 count=1 2>/dev/null | xxd

# 두 디스크 동기화 / 클론 (조심)
sudo dd if=/dev/sda of=/dev/sdb bs=4M status=progress conv=fdatasync
```

## 42.8 함정 / 안전 수칙

1. **`of=` 의 디바이스를 두 번 확인**. `lsblk`, `blkid`, mount 출력.
2. **항상 `bs=` 지정**. 기본 512 바이트는 매우 느림.
3. **`status=progress`** — 진행 안 보이면 끄고 싶어진다.
4. **dd 직후 sync** — `conv=fdatasync` 또는 `sync` 명령. 이미지 굽고 바로 뽑으면 데이터 손실.
5. **마운트 해제 후 작업** — 마운트 중 디스크 dd 는 일관성 깨짐.
6. **파티션 테이블 백업** — `sgdisk --backup`.
7. **손상 디스크는 dd 가 아니라 ddrescue**.
8. **노트북 디스크 → USB** 가 헷갈리면 `wipefs -a` 같은 안전 명령부터.

## 42.9 대안

| 의도 | dd 보다 나은 것 |
|------|-----------------|
| ISO 굽기 | `cp file.iso /dev/sdX` (현대 커널) 또는 `etcher`, `usbimager` |
| 파일 자르기 | `truncate`, `fallocate` |
| 디스크 클론 | `clonezilla`, `partclone`, `ddrescue` |
| 손상 복구 | `ddrescue` |
| 보안 와이프 | `shred`, `blkdiscard`, 제조사 secure erase |

다음 챕터: [제43장]

\newpage

---


# 43. apt / dpkg — Debian / Ubuntu 패키지 관리

> 데비안 계열의 표준. apt 는 사용자용 frontend, dpkg 는 저수준.

## 43.1 apt vs apt-get vs aptitude

| 도구 | 권장도 |
|------|--------|
| `apt` | **사용자 권장**. 깔끔한 출력, 진행률 |
| `apt-get` | 스크립트용 (안정된 인터페이스) |
| `apt-cache` | 검색/조회 (apt 가 통합) |
| `aptitude` | 풍부한 TUI, 의존성 해결 강력 |
| `synaptic` | GUI |

## 43.2 자주 쓰는 명령

```bash
# 인덱스 갱신
sudo apt update

# 전체 업그레이드
sudo apt upgrade
sudo apt full-upgrade               # 의존성 변경 허용 (구 dist-upgrade)

# 설치 / 제거
sudo apt install pkg
sudo apt install pkg1 pkg2
sudo apt install ./local.deb        # 로컬 파일
sudo apt install pkg=1.2.3-1        # 특정 버전
sudo apt install -y pkg             # yes 자동
sudo apt install --no-install-recommends pkg
sudo apt install --reinstall pkg

sudo apt remove pkg                 # 설정 보존
sudo apt purge pkg                  # 설정도 삭제
sudo apt autoremove                 # 더 이상 필요 없는 의존성

# 검색 / 정보
apt search keyword
apt show pkg
apt list --installed
apt list --upgradable
apt depends pkg
apt rdepends pkg

# 정리
sudo apt clean                      # 다운받은 .deb 삭제
sudo apt autoclean                  # 오래된 것만
```

자동화에는 `apt-get` 또는 `apt -y`. 인터랙티브 출력 안정성은 `apt-get`.

## 43.3 비밀번호 없이 자동화 (CI)

```bash
sudo DEBIAN_FRONTEND=noninteractive apt-get -y \
  -o Dpkg::Options::="--force-confdef" \
  -o Dpkg::Options::="--force-confold" \
  install pkg
```

| 옵션 | 의미 |
|------|------|
| `DEBIAN_FRONTEND=noninteractive` | 모든 설치 프롬프트 무시 |
| `-y` | yes |
| `Dpkg::Options::=--force-confold` | 설정파일 충돌 시 옛것 유지 |
| `Dpkg::Options::=--force-confnew` | 새것 채택 |

## 43.4 apt 소스 (저장소)

`/etc/apt/sources.list` + `/etc/apt/sources.list.d/*.list`:

```
deb http://archive.ubuntu.com/ubuntu jammy main universe multiverse restricted
deb http://archive.ubuntu.com/ubuntu jammy-updates main universe
deb http://security.ubuntu.com/ubuntu jammy-security main universe
```

`deb-src` 는 소스 패키지.

### 새 저장소 추가

```bash
# 옛 방식 (deprecated)
echo "deb https://example.com/repo focal main" | sudo tee /etc/apt/sources.list.d/myrepo.list
sudo apt-key add publickey.asc

# 현대 방식 (signed-by + keyring)
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://example.com/repo.gpg | sudo gpg --dearmor -o /etc/apt/keyrings/myrepo.gpg
echo "deb [signed-by=/etc/apt/keyrings/myrepo.gpg] https://example.com/repo focal main" \
  | sudo tee /etc/apt/sources.list.d/myrepo.list
sudo apt update
```

`apt-key` 는 deprecated. 항상 keyring 파일 + `signed-by`.

### PPA (Ubuntu)

```bash
sudo add-apt-repository ppa:user/ppa-name
sudo apt update
sudo apt install pkg
```

## 43.5 보류 / 특정 버전 고정

```bash
# 업그레이드 제외 (apt-mark)
sudo apt-mark hold pkg
sudo apt-mark unhold pkg
sudo apt-mark showhold

# 우선순위 (pinning)
# /etc/apt/preferences.d/myapp
Package: nginx
Pin: version 1.20.*
Pin-Priority: 1001
```

## 43.6 dpkg — 저수준

apt 는 결국 dpkg 에 위임. 직접 호출은 .deb 파일 처리에 자주.

```bash
sudo dpkg -i pkg.deb            # 설치
sudo dpkg -r pkg                # 제거 (apt remove 와 같음)
sudo dpkg -P pkg                # purge

dpkg -l                         # 설치 목록
dpkg -l '*nginx*'               # 패턴
dpkg -l | sed -n '/^ii/p'       # 정상 설치만

dpkg -L pkg                     # pkg 의 모든 파일
dpkg -S /usr/bin/python3        # 어느 패키지 소속?
dpkg -s pkg                     # 자세한 상태

dpkg-deb -c pkg.deb             # .deb 안 파일들
dpkg-deb -I pkg.deb             # 메타데이터
dpkg-deb -x pkg.deb extracted/  # 풀기

# 의존성 깨졌을 때
sudo apt --fix-broken install
sudo dpkg --configure -a
```

### 상태 코드 (`dpkg -l` 첫 컬럼)

```
ii  pkg  ver  installed
rc  pkg  ver  removed, config remains
un  pkg       not installed
```

## 43.7 보안 업데이트만

```bash
# 보안 출처에서 온 것만 업그레이드
sudo apt-get -y -o Dpkg::Options::='--force-confdef' \
  -o Dpkg::Options::='--force-confold' \
  -t $(lsb_release -cs)-security upgrade

# unattended-upgrades 활성화
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

`/etc/apt/apt.conf.d/50unattended-upgrades`:
```
Unattended-Upgrade::Allowed-Origins {
    "${distro_id}:${distro_codename}-security";
};
Unattended-Upgrade::Automatic-Reboot "false";
```

## 43.8 시스템 업그레이드 (do-release-upgrade)

```bash
sudo do-release-upgrade
sudo do-release-upgrade -d        # 개발 버전
```

LTS → LTS 사이가 보통 권장.

## 43.9 자주 쓰는 한 줄

```bash
# 가장 큰 설치 패키지
dpkg-query -Wf '${Installed-Size}\t${Package}\n' | sort -n | tail

# 설치된 패키지 백업
dpkg --get-selections > pkgs.list
# 복원
sudo apt update
sudo dpkg --set-selections < pkgs.list
sudo apt-get -y dselect-upgrade

# 어느 패키지가 이 명령을 제공?
dpkg -S /usr/bin/htop

# 명령이 깔리지 않았다면 어떤 패키지?
sudo apt install command-not-found
sudo apt update
htop                   # 안 깔렸으면 알려줌

# 한 패키지 의존성 트리
apt-rdepends pkg | head      # apt-rdepends 별도 설치

# 자동 설치된 / 수동 설치
apt-mark showauto
apt-mark showmanual

# 사용 안 하는 커널 정리
sudo apt autoremove --purge
sudo apt-get autoclean
```

## 43.10 apt 캐시 / 디스크

```bash
# 캐시 위치
ls /var/cache/apt/archives/
sudo du -sh /var/cache/apt/archives/

# 다운받은 .deb 다 삭제
sudo apt clean

# 더 이상 안 쓰는 .deb 만
sudo apt autoclean
```

## 43.11 함정

| 함정 | 대처 |
|------|------|
| `apt update` 인덱스만 갱신, 업그레이드 X | 둘은 다른 명령 |
| `apt remove` 후 설정 잔존 | `apt purge` |
| `apt-key` 안 됨 | keyring 파일 + signed-by |
| 새 PPA 추가 후 update 안 함 | 항상 update 한 번 |
| `dist-upgrade` 와 `upgrade` 차이 | upgrade 는 의존 변경 안 함 |
| 외부 .deb 의존성 깨짐 | `apt install ./pkg.deb` (자동 의존성) |
| 도커 컨테이너 안 cron 의 apt | DEBIAN_FRONTEND=noninteractive 필수 |
| `Pin-Priority` 잘못 → 다운그레이드 | 1001 이상이면 강제 |

다음 챕터: [제44장]

\newpage

---


# 44. dnf / yum / rpm — RHEL / Fedora 패키지

> RHEL/CentOS/Fedora/Rocky/Alma. dnf 가 yum 의 후계자. rpm 이 저수준.

## 44.1 yum vs dnf

- **yum**: 전통. RHEL 7 / CentOS 7 까지 기본
- **dnf**: yum 대체. RHEL 8+, Fedora. 더 빠르고 깔끔
- 호환: 대부분 동일 옵션

```bash
sudo dnf ...     # = sudo yum ...
```

## 44.2 자주 쓰는 명령

```bash
# 인덱스 (dnf 는 자동, 수동도 가능)
sudo dnf check-update
sudo dnf clean all
sudo dnf makecache

# 업그레이드
sudo dnf upgrade
sudo dnf upgrade --security
sudo dnf upgrade-minimal

# 설치 / 제거
sudo dnf install pkg
sudo dnf install pkg1 pkg2
sudo dnf install ./local.rpm
sudo dnf install pkg-1.2.3
sudo dnf reinstall pkg
sudo dnf remove pkg
sudo dnf autoremove

# 검색 / 정보
dnf search keyword
dnf info pkg
dnf list installed
dnf list available
dnf list updates
dnf provides */bin/htop          # 어느 패키지가 이 파일 제공?
dnf repoquery --whatprovides 'config(httpd)'

# 그룹
dnf grouplist
dnf groupinstall "Development Tools"
dnf groupinstall @web-server

# 의존성
dnf deplist pkg
dnf repoquery --requires pkg
dnf repoquery --whatrequires pkg
```

## 44.3 트랜잭션 / 히스토리

```bash
sudo dnf history
sudo dnf history info LAST
sudo dnf history undo NN          # 트랜잭션 NN 되돌리기
sudo dnf history rollback NN      # NN 시점으로
sudo dnf history redo NN
```

이 기능이 dnf 가 apt 보다 강력한 부분 — 모든 변경이 트랜잭션으로 추적.

## 44.4 모듈 / 스트림 (DNF 4+)

특정 소프트웨어의 여러 버전을 모듈로 제공.

```bash
sudo dnf module list                 # 사용 가능 목록
sudo dnf module list nodejs
sudo dnf module install nodejs:18
sudo dnf module enable postgresql:13
sudo dnf module disable postgresql:13
sudo dnf module reset nodejs
sudo dnf module switch-to nodejs:20
```

## 44.5 dnf5 (Fedora 41+)

```bash
sudo dnf5 install pkg
sudo dnf5 upgrade
sudo dnf5 history list
```

대부분 옵션이 호환. 더 빠르고 출력 깔끔.

## 44.6 저장소 (repos)

`/etc/yum.repos.d/*.repo`:

```ini
[base]
name=Base
baseurl=http://mirror.centos.org/centos/$releasever/os/$basearch/
gpgcheck=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-CentOS
enabled=1
```

추가:

```bash
sudo dnf config-manager --add-repo https://example.com/repo.repo
sudo dnf config-manager --enable repo-name
sudo dnf config-manager --disable repo-name
sudo dnf config-manager --setopt repo-name.priority=10
```

EPEL (Extra Packages):

```bash
sudo dnf install epel-release
sudo dnf install --enablerepo=epel htop
```

## 44.7 일시적으로 다른 저장소만

```bash
sudo dnf --disablerepo='*' --enablerepo=epel install htop
sudo dnf --enablerepo=updates-testing install pkg
```

## 44.8 rpm — 저수준

```bash
# 설치 / 업그레이드 / 제거
sudo rpm -ivh pkg.rpm        # install + verbose + hash
sudo rpm -Uvh pkg.rpm        # upgrade or install
sudo rpm -e pkg              # erase
sudo rpm -e --nodeps pkg     # 의존성 무시 (위험)

# 조회
rpm -qa                      # 모든 설치 패키지
rpm -qa | sort
rpm -q pkg                   # 설치 여부 + 버전
rpm -qi pkg                  # 정보
rpm -ql pkg                  # 파일 목록
rpm -qf /usr/bin/htop        # 어느 패키지?
rpm -qd pkg                  # 문서
rpm -qc pkg                  # 설정 파일
rpm -q --requires pkg
rpm -q --provides pkg
rpm -q --whatrequires pkg
rpm -q --scripts pkg         # 설치/제거 스크립트
rpm -q --changelog pkg | head

# 검증 (변경 점검)
rpm -V pkg                   # 변경된 파일
rpm -Va                      # 모든 패키지 검증
sudo rpm --setperms pkg      # 권한 복원
sudo rpm --setugids pkg

# .rpm 파일 정보
rpm -qip pkg.rpm
rpm -qlp pkg.rpm
rpm2cpio pkg.rpm | cpio -idmv  # 풀기
```

### rpm -V 의 출력 코드

```
S.5....T.  c /etc/myconf.conf
```

| 위치 | 의미 |
|------|------|
| S | 크기 다름 |
| M | 모드 (권한) 다름 |
| 5 | MD5 다름 |
| D | 디바이스 |
| L | 심볼릭링크 |
| U | 사용자 |
| G | 그룹 |
| T | mtime |
| P | capability |

`c` = config 파일.

## 44.9 자동 보안 업데이트

```bash
sudo dnf install dnf-automatic
sudo systemctl enable --now dnf-automatic.timer
```

`/etc/dnf/automatic.conf`:

```ini
[commands]
upgrade_type = security
download_updates = yes
apply_updates = yes
```

## 44.10 자주 쓰는 한 줄

```bash
# 가장 큰 패키지
rpm -qa --queryformat "%{SIZE} %{NAME}\n" | sort -n | tail

# 어느 저장소에서 왔나
dnf list --installed pkg
dnf repolist

# 설치된 모든 패키지의 라이선스 정보
rpm -qa --queryformat "%{NAME}: %{LICENSE}\n" | sort

# 어떤 명령이 어느 패키지?
dnf provides /usr/bin/htop
dnf provides '*/bin/htop'

# 보안 업데이트만 보기
dnf updateinfo list security
dnf updateinfo info security

# 패키지가 만든 변경 (config 빼고) 복원
sudo rpm --setperms pkg
sudo rpm --setugids pkg

# 한 패키지의 설정 파일 변경분만
rpm -V pkg | sed -n '/^.....c/p'

# 트랜잭션 로그
sudo dnf history list
sudo dnf history info 42
```

## 44.11 createrepo — 사설 저장소

```bash
sudo dnf install createrepo

# 디렉토리에 .rpm 모은 후
mkdir -p /srv/repo
cp *.rpm /srv/repo/
createrepo /srv/repo/

# nginx / apache 로 노출
# 클라이언트:
# /etc/yum.repos.d/local.repo
[local]
name=Local
baseurl=http://repo.example.com/repo/
gpgcheck=0
enabled=1
```

## 44.12 함정

| 함정 | 대처 |
|------|------|
| `rpm -e --nodeps` 남발 | 의존성 깨짐 → dnf 가 못 고침 |
| 외부 .rpm 의존성 깨짐 | `dnf install ./pkg.rpm` (자동 의존성) |
| GPG 검증 실패 | 키 등록, 또는 `--nogpgcheck` (위험) |
| 모듈 활성/비활성 후 reset 안 함 | `dnf module reset NAME` |
| EPEL 활성 후 의존 충돌 | `--enablerepo=epel` 로 임시만 |
| dnf clean all 후 첫 install 느림 | 메타데이터 새로 받음 |
| RHEL subscription 만료 | subscription-manager 점검 |

다음 챕터: [제45장]

\newpage

---


# 45. pacman / AUR / pkg (Termux)

> 아치 리눅스 계열의 빠르고 단순한 패키지 매니저. + Termux 보너스.

## 45.1 pacman 기본 (Arch / Manjaro / EndeavourOS)

```bash
# 인덱스 + 모든 패키지 업그레이드 (둘이 항상 같이!)
sudo pacman -Syu

# 설치
sudo pacman -S pkg
sudo pacman -S pkg1 pkg2

# 검색
pacman -Ss keyword
pacman -Si pkg              # 저장소 정보
pacman -Qi pkg              # 설치된 패키지 정보

# 제거
sudo pacman -R pkg            # 의존성 보존
sudo pacman -Rs pkg           # 의존성도 (다른 패키지가 안 쓰면)
sudo pacman -Rns pkg          # + 설정 파일

# 캐시 / 정리
sudo pacman -Sc               # 안 쓰는 캐시
sudo pacman -Scc              # 모든 캐시 (조심)
paccache -rk2                 # 마지막 2개 버전만 (pacman-contrib)

# 로컬 .pkg.tar.zst 설치
sudo pacman -U pkg.pkg.tar.zst
sudo pacman -U https://example.com/pkg.pkg.tar.zst
```

### 자주 쓰는 옵션 한눈에

| 옵션 | 의미 |
|------|------|
| `-S` | sync (저장소에서 설치) |
| `-Sy` | + 인덱스 갱신 |
| `-Syu` | + 시스템 업그레이드 |
| `-Ss` | 검색 |
| `-Si` | 저장소 정보 |
| `-Sw` | 다운로드만 |
| `-R` | 제거 |
| `-Rs` | + 안 쓰는 의존성 |
| `-Rn` | + 백업 안 함 |
| `-Q` | 로컬 쿼리 |
| `-Qe` | 명시적 설치 |
| `-Qm` | 외부 (AUR 등) |
| `-Qo FILE` | 어느 패키지 소속? |
| `-Ql pkg` | 파일 목록 |
| `-Qk pkg` | 무결성 검증 |
| `-Qdt` | 의존성 고아 |
| `-U` | 로컬 파일 설치 |
| `--noconfirm` | yes 자동 |
| `--needed` | 이미 최신이면 건너뜀 |

## 45.2 자주 쓰는 한 줄

```bash
# 모든 패키지 업그레이드 (정공법)
sudo pacman -Syu

# 부분 업그레이드 절대 금지: pacman -Sy pkg ❌
# (Arch 의 rolling release 모델은 항상 풀 sync)

# 의존성 고아 제거
sudo pacman -Rns $(pacman -Qdtq)

# 어느 패키지가 이 명령?
pacman -Qo /usr/bin/htop

# 패키지의 설정 파일들
pacman -Qii htop | grep '^Backup'

# 가장 큰 설치 패키지
LANG=C pacman -Qi | awk '/^Name/{n=$3} /Installed Size/{print $4,$5,n}' | sort -h | tail

# 업그레이드 후 변경 로그
pacman -Qu     # 업그레이드 가능 목록

# 파일 검증
pacman -Qkk pkg              # 강한 검증

# 미러 갱신 (한국 우선)
sudo reflector --country 'South Korea,Japan' --age 12 \
  --protocol https --sort rate --save /etc/pacman.d/mirrorlist
sudo pacman -Syyu
```

## 45.3 AUR — Arch User Repository

공식 저장소에 없는 패키지(서드파티 / 스냅샷)는 AUR.

### AUR helper (yay 권장)

```bash
# 처음 한 번
sudo pacman -S --needed git base-devel
git clone https://aur.archlinux.org/yay.git
cd yay
makepkg -si

# 그 후
yay -S pkg                  # AUR + 공식 둘 다 검색/설치
yay -Syu                    # 시스템 + AUR 통합
yay -Ss keyword
yay -Yc                     # 정리 (안 쓰는 의존성)
yay -Ps                     # 통계
```

`paru` 도 인기 (러스트, 더 빠름):

```bash
yay -S paru
paru -Syu
```

### AUR 직접 (helper 없이)

```bash
git clone https://aur.archlinux.org/pkg.git
cd pkg
less PKGBUILD       # 반드시 검토!
makepkg -si         # 빌드 + 설치
```

`PKGBUILD` 가 셸 스크립트라 임의 명령 실행. 신뢰 안 가는 패키지는 절대 보지 않고 install 하지 말 것.

## 45.4 pacman 설정

`/etc/pacman.conf`:

```ini
[options]
HoldPkg     = pacman glibc
Architecture = auto
Color
ParallelDownloads = 5
CheckSpace
VerbosePkgLists
ILoveCandy

[core]
Include = /etc/pacman.d/mirrorlist

[extra]
Include = /etc/pacman.d/mirrorlist

[multilib]
Include = /etc/pacman.d/mirrorlist
```

`ILoveCandy` — 진행 막대를 팩맨으로.

미러 리스트 `/etc/pacman.d/mirrorlist` 우선순위 확인 / 갱신 (`reflector`).

## 45.5 키링 / 신뢰

```bash
sudo pacman-key --init
sudo pacman-key --populate archlinux
sudo pacman-key --refresh-keys
```

업그레이드 후 GPG 에러 나면:

```bash
sudo pacman -Sy archlinux-keyring
sudo pacman -Syu
```

## 45.6 부분 업그레이드 금지

```bash
# 위험! ❌
sudo pacman -Sy pkg            # 다른 패키지가 새 의존성을 깨뜨릴 수 있음

# 정답 ✅
sudo pacman -Syu               # 항상 풀 업그레이드
sudo pacman -S pkg             # 인덱스 그대로면 OK
```

Arch 는 rolling release 라 부분 업데이트가 깨진다. 모든 패키지 함께.

## 45.7 시스템 복구

```bash
# 손상된 패키지 재설치
sudo pacman -S --overwrite '*' pkg

# 모든 명시 패키지 재설치
pacman -Qqen | sudo pacman -S --needed -

# 부팅 안 되면 라이브 USB → arch-chroot
mount /dev/sdaX /mnt
arch-chroot /mnt
pacman -Syu
```

## 45.8 Termux pkg

안드로이드용. 사실상 apt 의 wrapper.

```bash
pkg update
pkg upgrade
pkg install openssh
pkg search keyword
pkg show pkg
pkg list-installed
pkg autoclean

# 저장소 변경
termux-change-repo

# 카테고리
pkg install root-repo       # root 도구
pkg install x11-repo        # X 윈도우
pkg install game-repo
```

내부적으로 `apt`/`dpkg` 가 동작. Termux 환경 변수 (`$PREFIX`):

```bash
echo $PREFIX
# /data/data/com.termux/files/usr
```

대부분의 리눅스 도구가 동작하지만 일부는 안드로이드 보안 모델로 제약 (e.g. ping 은 root 만, mount 일부 안 됨).

## 45.9 Flatpak / Snap (덤)

배포판 무관 사용자 영역 패키지.

### Flatpak

```bash
sudo apt install flatpak
flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo

flatpak search keyword
flatpak install flathub org.gnome.gedit
flatpak run org.gnome.gedit
flatpak update
flatpak list
flatpak uninstall org.gnome.gedit
```

### Snap

```bash
sudo apt install snapd
sudo snap install pkg
sudo snap refresh
sudo snap remove pkg
snap list
```

운영 도구는 보통 시스템 패키지 매니저, 데스크탑 앱은 flatpak 권장 의견 多.

## 45.10 자주 쓰는 한 줄

```bash
# 명시적 설치 패키지 백업 (재설치 시 복원)
pacman -Qqe > pkglist.txt
# AUR 만
pacman -Qqem > aurlist.txt

# 복원
sudo pacman -S --needed - < pkglist.txt
yay -S --needed - < aurlist.txt

# 안 쓰는 의존성
pacman -Qdt
sudo pacman -Rns $(pacman -Qdtq)

# 가장 최근 설치된 패키지 톱
expac --timefmt='%Y-%m-%d %H:%M' '%l\t%n' | sort | tail

# 라이선스
expac '%l %n' | sort -u

# 만든 사람 / 빌드 정보
pacman -Qi pkg | head
```

## 45.11 함정

| 함정 | 대처 |
|------|------|
| 부분 업그레이드 (`-Sy pkg`) | 항상 `-Syu` |
| AUR PKGBUILD 검토 안 함 | 항상 less 로 보기 |
| 키링 만료 | `archlinux-keyring` 우선 |
| 미러 느림 | `reflector` |
| 캐시 폭주 | `paccache -rk2` cron |
| 부팅 안 됨 | 라이브 USB → chroot 복구 |
| Termux 의 `apt-get update` 시 sources.list | `termux-change-repo` |

다음 챕터: [제46장]

\newpage

---


# 46. date, watch, sleep, time, timeout

> 시간 다루기와 반복 / 측정.

## 46.1 date — 현재 시간

```bash
date                            # 기본
date -u                         # UTC
date +%Y-%m-%d                  # 2026-05-07
date +%Y-%m-%dT%H:%M:%S
date -Iseconds                  # ISO 8601
date -R                         # RFC 2822 (메일)
date +%s                        # epoch
date +%s%N                      # 나노초
```

### 포맷

| 토큰 | 의미 |
|------|------|
| `%Y` | 4자리 연도 |
| `%y` | 2자리 |
| `%m` | 월 |
| `%d` | 일 |
| `%H` | 시 (00-23) |
| `%I` | 시 (01-12) |
| `%M` | 분 |
| `%S` | 초 |
| `%N` | 나노초 |
| `%j` | 연중 일수 |
| `%a` | 요일 약자 |
| `%A` | 요일 |
| `%b` | 월 약자 |
| `%B` | 월 |
| `%Z` | 타임존 약자 |
| `%z` | 타임존 +0900 |
| `%s` | epoch |
| `%F` | %Y-%m-%d |
| `%T` | %H:%M:%S |
| `%R` | %H:%M |

### 상대 / 임의 시각

```bash
date -d 'tomorrow'
date -d 'yesterday'
date -d 'next monday'
date -d '5 days ago'
date -d '2 hours ago'
date -d '2026-12-31 18:00'
date -d '@1700000000'                # epoch → 사람
date -d '2026-12-31' +%s             # 사람 → epoch

# 차이 계산
A=$(date -d '2026-05-01' +%s)
B=$(date -d '2026-05-07' +%s)
echo $(( (B - A) / 86400 ))          # 일 수
```

### 시스템 시간 변경

```bash
# 즉시 (NTP 비활성 상태에서만)
sudo date -s '2026-05-07 09:00:00'

# 보통은 timedatectl
sudo timedatectl set-time '2026-05-07 09:00:00'
sudo timedatectl set-timezone Asia/Seoul
sudo timedatectl set-ntp true
timedatectl status
```

```bash
# 하드웨어 시계
sudo hwclock --show
sudo hwclock --hctosys      # HW → 시스템
sudo hwclock --systohc      # 시스템 → HW
```

## 46.2 timezone

```bash
timedatectl list-timezones | grep -i seoul
sudo timedatectl set-timezone Asia/Seoul

# 임시
TZ=UTC date
TZ=America/Los_Angeles date

# 환경 변수로 영구
echo 'export TZ=Asia/Seoul' >> ~/.bashrc
```

## 46.3 cal — 달력

```bash
cal                # 이번 달
cal 5 2026         # 2026년 5월
cal -3             # 전, 현재, 다음 달
cal -y 2026        # 한 해
cal -w             # 주 번호 표시
cal -m             # 월요일 시작 (보통 일요일)
ncal -b            # block 스타일

# 한국 공휴일은 별도 도구 (calendar 패키지의 daniels?, 또는 ical)
```

## 46.4 sleep — 대기

```bash
sleep 5            # 5초
sleep 0.5          # 0.5초 (GNU)
sleep 5m           # 5분 (GNU: s/m/h/d)
sleep 1h
sleep 1d

# 다중 (합)
sleep 1m 30s       # GNU: 합 = 90초

# 정확한 시각까지
sleep $(( $(date -d '09:00' +%s) - $(date +%s) ))
```

`busybox` sleep 은 단위 안 받음 → 초만.

## 46.5 watch — 주기적 실행

```bash
watch CMD
watch -n 1 'date'                  # 1초마다
watch -n 0.5 'ss -ltn'             # 0.5초
watch -d 'free -h'                 # 차이 강조
watch -d=permanent CMD             # 차이 누적
watch -c CMD                       # 색 보존 (-c = ANSI)
watch -t CMD                       # 헤더 끔
watch -b CMD                       # 비프 (종료 코드 0 아닐 때)
watch -e CMD                       # 종료 코드 0 아니면 종료
watch -g CMD                       # 출력이 변하면 종료
```

```bash
# 디스크 사용량 변화 추적
watch -d -n 5 'df -h /'

# 특정 프로세스 메모리 변화
watch -d 'ps -p PID -o pid,vsz,rss,cmd'

# k8s pod 상태
watch kubectl get pods

# 한 번 변하면 알림
watch -g 'pgrep myproc' && notify-send "myproc 살아남"
```

## 46.6 time — 명령 시간 측정

두 가지 `time`:

```bash
type time             # bash builtin 인지 외부 (/usr/bin/time)
```

### bash builtin

```bash
time cmd
# real    0m1.234s
# user    0m0.500s
# sys     0m0.100s
```

| 항목 | 의미 |
|------|------|
| real | wall time |
| user | CPU 시간 (사용자 공간) |
| sys | CPU 시간 (커널) |

### /usr/bin/time

더 풍부:

```bash
/usr/bin/time -v cmd
# Maximum resident set size, Page faults, ...

/usr/bin/time -f '%e %M' cmd       # 사용자 포맷
/usr/bin/time -o time.log cmd
```

## 46.7 timeout — 시간 제한

```bash
timeout 10 cmd                     # 10초 후 SIGTERM
timeout 10s cmd
timeout 5m cmd
timeout --kill-after=5 30 cmd      # 30초 → SIGTERM, 그 후 5초 → SIGKILL
timeout -s SIGINT 10 cmd
timeout --preserve-status 10 cmd   # 종료 코드 cmd 의 것 그대로

# 종료 코드 124 = 타임아웃
timeout 3 sleep 10; echo $?        # → 124
```

자동화에서 매우 유용:

```bash
if ! timeout 30 ./test.sh; then
  echo "test took too long"
fi
```

## 46.8 자주 쓰는 한 줄

```bash
# 어제 / 내일 날짜
yesterday=$(date -d 'yesterday' +%F)
tomorrow=$(date -d 'tomorrow' +%F)

# 백업 파일 이름
bak="backup-$(date +%F-%H%M%S).tgz"

# 주차 (ISO)
date +%V        # ISO 주
date +%U        # 일요일 시작 주
date +%W        # 월요일 시작 주

# 30일 전 epoch
date -d '30 days ago' +%s

# 두 시각 사이 초
echo $(( $(date -d "$T2" +%s) - $(date -d "$T1" +%s) ))

# 구간 동안 N초마다 실행
END=$(date -d '5 min' +%s)
while [ $(date +%s) -lt $END ]; do
  curl -s healthcheck.url
  sleep 30
done

# 명령 평균 실행 시간 (5회)
for i in {1..5}; do /usr/bin/time -f '%e' cmd 2>&1 >/dev/null; done | \
  awk '{s+=$1} END{print s/NR}'

# 시계 동기 점검
chronyc tracking
chronyc sources

# UTC 와 로컬 동시 표시
echo "UTC : $(date -u +%FT%TZ)"
echo "KST : $(date +%FT%T%z)"
```

## 46.9 chrony / NTP

```bash
sudo apt install chrony
sudo systemctl enable --now chrony
chronyc tracking
chronyc sources
chronyc makestep            # 즉시 큰 점프 적용

# systemd-timesyncd (가벼움)
timedatectl
sudo timedatectl set-ntp true
```

`timedatectl status` 의 `System clock synchronized: yes` 확인.

## 46.10 함정

| 함정 | 대처 |
|------|------|
| `date -d` GNU 만 | macOS는 `gdate`(coreutils) 또는 `-j -f` |
| `sleep 1m` 단위 BusyBox 안 먹음 | 초로 |
| `time` builtin vs /usr/bin/time | 자세한 정보 후자 |
| `watch` 가 셸 별칭 못 봄 | `watch -x` 또는 셸로 감싸기 |
| 시계 큰 차이 → SSL/Kerberos 깨짐 | NTP 강제 |
| 과거 시각 변경 | 운영 중 매우 위험 (cron, log) |

다음 챕터: [제47장]

\newpage

---


# 47. history, alias, env, export — 셸 환경

> 자주 치는 명령은 짧게, 자주 쓰는 값은 변수로.

## 47.1 history — 명령 기록

```bash
history                  # 전체
history 50               # 최근 50개
history -d 100           # 100번 줄 삭제
history -c               # 메모리 기록 비움 (파일은 그대로)
history -w               # 메모리 → 파일 즉시 저장
history -r               # 파일 → 메모리
history -a               # 메모리 새 항목만 파일에 추가
```

기본 위치: `~/.bash_history` (bash), `~/.zsh_history` (zsh).

### 핵심 단축키

| 키 | 동작 |
|----|------|
| `Ctrl+R` | 역방향 incremental 검색 |
| `Ctrl+S` | 정방향 (`stty -ixon` 필요) |
| `Ctrl+G` | 검색 취소 |
| `Ctrl+P` / `↑` | 이전 명령 |
| `Ctrl+N` / `↓` | 다음 명령 |
| `Alt+.` | 직전 명령의 마지막 인자 |
| `!!` | 직전 명령 |
| `!N` | N번째 |
| `!STR` | STR 로 시작하는 가장 최근 |
| `!?STR?` | STR 포함하는 |
| `^a^b` | 직전 명령에서 a→b 치환 후 실행 |
| `!:^` | 첫 인자 |
| `!:$` | 마지막 인자 |
| `!:*` | 모든 인자 |

```bash
ls /etc/passwd
sudo !!                  # → sudo ls /etc/passwd

vim long/path/to/file.txt
ls -l !$                 # → ls -l long/path/to/file.txt
```

### 환경 변수

```bash
export HISTSIZE=100000
export HISTFILESIZE=200000
export HISTCONTROL=ignoredups:erasedups
export HISTTIMEFORMAT='%F %T '       # 시각 prefix
export HISTIGNORE='ls:cd:exit:history:pwd'
shopt -s histappend                  # 종료 시 append (덮어쓰지 않음)

# 다중 셸 동기화
PROMPT_COMMAND='history -a; history -c; history -r; '$PROMPT_COMMAND
```

zsh:

```zsh
HISTSIZE=100000
SAVEHIST=200000
HISTFILE=~/.zsh_history
setopt SHARE_HISTORY EXTENDED_HISTORY HIST_IGNORE_ALL_DUPS HIST_IGNORE_SPACE
```

명령 앞에 공백 두면 (`HISTCONTROL`에 ignorespace 또는 ignoreboth) history 안 들어감 → 비밀번호 입력 시 유용.

## 47.2 alias — 명령 별칭

```bash
alias                            # 모두 보기
alias ll='ls -lah'
alias gs='git status'
alias gd='git diff'
alias ..='cd ..'
alias ...='cd ../..'
alias g='grep --color=auto'
alias myip='curl -s ifconfig.me'
alias ports='sudo ss -tulnp'

unalias gs
unalias -a                       # 모두 제거 (이번 셸만)
```

영구 저장: `~/.bashrc` / `~/.zshrc`.

### 자주 쓰는 alias 모음

```bash
# 안전판
alias rm='rm -i'
alias cp='cp -i'
alias mv='mv -i'

# 빠른 점프
alias ..='cd ..'
alias ...='cd ../..'
alias ....='cd ../../..'

# 보기
alias ll='ls -lAh'
alias l='ls -lh'
alias la='ls -A'
alias lt='ls -lAhrt'         # 시간 정렬

# 시스템
alias df='df -h'
alias du='du -h'
alias free='free -h'
alias ps='ps -ef'
alias mount='mount | column -t'
alias path='echo -e ${PATH//:/\\n}'

# git
alias g='git'
alias gst='git status -s'
alias gd='git diff'
alias gco='git checkout'
alias gp='git push'
alias gl='git pull'
alias glog='git log --oneline --graph --decorate --all'

# 안전 sudo
alias please='sudo'

# 새 명령 생성
alias mkcd='function _mkcd(){ mkdir -p "$1" && cd "$1"; }; _mkcd'
```

### 함수 vs alias

함수가 더 강력 (인자 위치 등):

```bash
mkcd() { mkdir -p "$1" && cd "$1"; }
gz() { tar czf "$1.tgz" "$1"; }
extract() {
  case "$1" in
    *.tar.gz|*.tgz) tar xzf "$1" ;;
    *.tar.bz2)      tar xjf "$1" ;;
    *.tar.xz)       tar xJf "$1" ;;
    *.zip)          unzip "$1" ;;
    *.7z)           7z x "$1" ;;
    *) echo "지원 안 함: $1" ;;
  esac
}
```

## 47.3 env, export, set, unset

### 변수 설정

```bash
NAME=alice                          # 셸 변수 (자식 안 봄)
export NAME=alice                   # 환경 변수 (자식도 봄)
export PATH="$PATH:/opt/bin"
unset NAME                          # 제거
NAME=alice cmd                      # cmd 한 번에만 export
```

### 환경 보기

```bash
env                       # 환경변수
printenv                  # 동일
printenv PATH
env | sort
set                       # 셸 변수 + 함수 (bash/zsh)
declare -p                # 자세한 타입
declare -p PATH

# 빈 환경에서 실행
env -i CMD
env -i HOME="$HOME" PATH=/usr/bin /bin/sh
```

### 자주 쓰는 환경 변수

| 변수 | 용도 |
|------|------|
| `PATH` | 명령 검색 경로 |
| `HOME` | 홈 |
| `USER` `LOGNAME` | 사용자 |
| `SHELL` | 로그인 셸 |
| `TERM` | 단말 종류 |
| `LANG` `LC_ALL` | 로케일 |
| `EDITOR` `VISUAL` | 기본 에디터 |
| `PAGER` | 기본 페이저 (보통 less) |
| `LESS` | less 옵션 |
| `MANPAGER` | man 페이저 |
| `TZ` | 타임존 |
| `XDG_CONFIG_HOME` | 사용자 설정 |
| `XDG_DATA_HOME` | 사용자 데이터 |
| `XDG_CACHE_HOME` | 사용자 캐시 |
| `SSH_AUTH_SOCK` | ssh-agent 소켓 |
| `HISTSIZE` `HISTFILE` `HISTCONTROL` | history |

### PATH 다루기

```bash
# 추가 (앞에 = 우선)
export PATH="/opt/bin:$PATH"

# 뒤에
export PATH="$PATH:/opt/bin"

# 중복 제거
export PATH=$(echo "$PATH" | awk -v RS=: -v ORS=: '!a[$0]++' | sed 's/:$//')

# 보기
echo $PATH | tr ':' '\n'
```

## 47.4 source / .

```bash
source ~/.bashrc
. ~/.bashrc                  # POSIX

# 다른 스크립트의 변수/함수 로드
source ~/scripts/lib.sh
```

`source` 는 현재 셸에서 실행 → 변수 변화가 유지됨. 일반 실행은 자식 셸이라 변화가 사라짐.

## 47.5 셸 시작 파일

bash:

| 파일 | 시점 |
|------|------|
| `/etc/profile` | 로그인 셸 |
| `/etc/bash.bashrc` | 비로그인 인터랙티브 |
| `~/.profile` | 로그인 (bashrc 로 위임 흔함) |
| `~/.bash_profile` 또는 `~/.bash_login` | 로그인 |
| `~/.bashrc` | 비로그인 인터랙티브 |
| `~/.bash_logout` | 로그아웃 |

규칙:
- **로그인 셸** (ssh, console): `/etc/profile` → `~/.bash_profile` (또는 `~/.profile`)
- **인터랙티브 비로그인** (terminal 안): `/etc/bash.bashrc` → `~/.bashrc`

`~/.bash_profile`가 흔히 `~/.bashrc`를 source.

```bash
# ~/.bash_profile
[ -f ~/.bashrc ] && . ~/.bashrc
```

zsh:

| 파일 | 시점 |
|------|------|
| `/etc/zshenv`, `~/.zshenv` | 모든 셸 |
| `/etc/zprofile`, `~/.zprofile` | 로그인 |
| `/etc/zshrc`, `~/.zshrc` | 인터랙티브 |
| `/etc/zlogin`, `~/.zlogin` | 로그인 (마지막) |
| `~/.zlogout` | 로그아웃 |

## 47.6 셸 옵션 (set, shopt)

```bash
# 강력한 디폴트 (스크립트)
set -e        # 에러 시 종료
set -u        # 미정의 변수 에러
set -x        # 명령 출력 (디버그)
set -o pipefail   # 파이프 일부 실패도 실패
set -euo pipefail

# 끄기
set +e
set +x

# bash 추가 옵션
shopt -s histappend
shopt -s checkwinsize
shopt -s globstar         # ** 활성
shopt -s nullglob         # 매치 없으면 빈 결과
shopt -s extglob          # 확장 글로브
shopt -s nocaseglob       # 대소문자 무시
shopt -s autocd           # 디렉토리만 입력해도 cd
```

## 47.7 자주 쓰는 한 줄

```bash
# 패스워드 입력 history 안 남기기
 mysql -u root -p     # 첫 글자 앞 공백 (HISTCONTROL=ignoreboth 일 때)

# 자주 쓰는 디렉토리 변수로
export PRJ=~/projects/myapp
cd $PRJ

# 자식이 못 보는 변수
SECRET="abc"; cmd                # cmd 안 보임
SECRET="abc" export SECRET; cmd  # 보임

# 부모 환경 그대로
sudo -E cmd

# 매 셸에서 다른 사용자 식별
export PS1='\[\e[1;32m\]\u@\h\[\e[0m\]:\[\e[1;34m\]\w\[\e[0m\]\$ '

# 로그인 셸이지 확인
shopt -q login_shell && echo "login" || echo "non-login"

# 모든 alias / 함수 한번에 보기
alias
declare -F          # 함수 이름
declare -f myfunc   # 함수 본문

# 셸 빠르게 갈아탐
chsh -s /bin/zsh

# 직전 명령 다시 sudo
sudo $(history -p '!!')
```

## 47.8 함정

| 함정 | 대처 |
|------|------|
| `export` 안 하면 자식 못 봄 | `export` 또는 `KEY=VAL cmd` |
| `~/.bashrc` 가 비로그인만 → SSH 시 안 읽힘 | `~/.profile` 에서 source |
| `set -e` 가 일부 사례 못 잡음 | `pipefail`, 명시적 `|| return 1` |
| alias 가 스크립트에서 안 동작 | bash: `shopt -s expand_aliases` |
| history 가 다른 셸에서 안 보임 | `PROMPT_COMMAND` 동기화 |
| 비밀번호가 history 에 들어감 | 첫 글자 공백, ignoreboth |
| TZ 변경 후 cron 영향 X | systemd 재시작 또는 재로그인 |

다음 챕터: [제48장]

\newpage

---


# 48. man, info, apropos, tldr

> 매뉴얼이 곧 진실. 어떻게 빠르게 찾고 효율적으로 읽나.

## 48.1 man

```bash
man cmd                    # 매뉴얼
man 5 passwd               # 섹션 5 (config 파일)
man -k keyword             # = apropos
man -K keyword             # 모든 매뉴얼 본문에서 검색 (느림)
man -f cmd                 # = whatis (한 줄 요약)
man -w cmd                 # 매뉴얼 파일 경로
man -a cmd                 # 모든 섹션 차례로
man --regex 'pat' .        # 정규식
man -P less cmd            # 페이저 지정
```

### 섹션 번호

| 번호 | 의미 |
|------|------|
| 1 | 사용자 명령 |
| 2 | 시스템 콜 |
| 3 | 라이브러리 함수 (C, perl, ...) |
| 4 | 디바이스 파일 |
| 5 | 파일 포맷 / 설정 |
| 6 | 게임 |
| 7 | 일반 (regex, signal, ...) |
| 8 | 관리자 명령 |

`man printf` 와 `man 3 printf` 는 다르다 (사용자 명령 vs C 함수).

```bash
man 7 signal               # 시그널 일반
man 7 socket
man 7 capabilities
man 5 sshd_config
man 5 fstab
```

### 페이저 안에서 (less)

| 키 | 동작 |
|----|------|
| `Space` / `f` | 다음 페이지 |
| `b` | 이전 페이지 |
| `g` `G` | 처음/끝 |
| `/PAT` | 검색 |
| `n` `N` | 다음/이전 매치 |
| `q` | 종료 |
| `h` | 도움말 |

`MANPAGER` 로 변경 가능:

```bash
export MANPAGER='less -R'
# 또는 화려하게
export MANPAGER="sh -c 'col -bx | bat -l man -p'"
```

## 48.2 apropos / whatis

```bash
apropos network                   # 매뉴얼 한 줄 설명에서 검색
apropos -s 8 network              # 섹션 8 만
whatis ssh                        # 한 줄 요약
whatis ssh sshd
```

매뉴얼이 갱신되면 인덱스도:

```bash
sudo mandb
```

## 48.3 info

GNU 도구는 종종 `man` 보다 `info` 가 더 자세하다.

```bash
info coreutils
info ls
info bash
```

### 인터랙티브 키

| 키 | 동작 |
|----|------|
| `Space` / `↓` | 스크롤 |
| `n` / `p` | 다음/이전 노드 |
| `u` | 위 (parent) |
| `Enter` | 링크 따라가기 |
| `l` | 이전 위치 |
| `q` | 종료 |
| `g` | go to (노드 이름) |
| `s` | 검색 |

man → info 통합:

```bash
pinfo bash      # vim 키 (vim/less 익숙한 사람)
```

## 48.4 tldr — 짧은 예제 모음

```bash
sudo apt install tldr        # 또는 npm i -g tldr
# 첫 번째 실행 시 캐시 받음
tldr update
tldr tar
tldr ssh
tldr -p linux find
```

긴 매뉴얼 대신 **자주 쓰는 예제 위주** 1 페이지. 외운 명령 빠르게 복기에 최고.

```
$ tldr tar

  Archiving utility...

  - Create a gzipped archive:
    tar czf target.tar.gz file1 file2

  - Extract:
    tar xzf source.tar.gz
  ...
```

`cheat`, `bro`, `eg` 도 비슷한 도구.

## 48.5 cmd --help

대부분의 명령이 `--help` 또는 `-h`:

```bash
cmd --help | head
cmd -h
cmd --help 2>&1 | less
```

short. man 까지 갈 일 아닐 때.

## 48.6 자주 쓰는 한 줄

```bash
# 설치된 모든 명령 목록
ls /usr/bin /usr/local/bin /usr/sbin | sort -u | less

# 어디서 왔는지 + 매뉴얼 위치
type cmd
which cmd
man -w cmd

# 매뉴얼 PDF 로
man -t ls | ps2pdf - ls.pdf

# 한 페이지 텍스트로 저장
man cmd | col -b > cmd.txt

# 함수/매크로 (C)
man 3 strcpy
man 2 read

# 시그널 사전
man 7 signal

# 셸 builtin
help cd                  # bash 빌트인 도움말
help [[
help test
```

## 48.7 매뉴얼 검색 전략

1. `tldr CMD` — 흔한 사용 예제 빠르게
2. `cmd --help | head -50` — 옵션 요약
3. `man cmd` — 전체. `/PAT` 으로 옵션 점프
4. `man -k keyword` — 키워드로 어떤 매뉴얼 있는지
5. `info cmd` — GNU 도구는 더 자세
6. 검색엔진 / 공식 문서 — 그래도 부족할 때

## 48.8 매뉴얼이 부족할 때

- `/usr/share/doc/PKG/` — 패키지 문서
- `/etc/PKG/` — 예제 설정
- `cheat.sh` — `curl cheat.sh/CMD`

```bash
curl cheat.sh/tar
curl cheat.sh/ssh
curl 'cheat.sh/find~delete'    # 흥미로운 검색
```

## 48.9 한국어 매뉴얼

```bash
sudo apt install manpages-ko         # debian
sudo dnf install man-pages-ko        # rhel
LC_ALL=ko_KR.UTF-8 LANG=ko_KR.UTF-8 man ls
```

번역이 옛 버전이거나 부족 → 영어 원본 권장.

## 48.10 함정

| 함정 | 대처 |
|------|------|
| `man cmd` 가 없음 | `cmd --help`, `info cmd`, `tldr cmd` |
| 같은 이름 다른 섹션 | `man -a cmd` 또는 명시 (`man 5 ...`) |
| `apropos` 가 빈 결과 | `sudo mandb` |
| 일부 패키지가 매뉴얼 미포함 | 별도 `cmd-doc` 패키지 또는 `/usr/share/doc/cmd/` |
| 비ASCII 매뉴얼 깨짐 | `LANG`, `LC_ALL` 확인 |

---

**부록 — 핸드북 마무리**

이 책은 "거의 모든 일을 CLI 한 줄로" 라는 목표 아래 SSH·rsync·자동화·진단·관리·시간·매뉴얼까지 두루 다뤘다. 이제부터의 깊이는 다음 단계의 자료에서:

- **셸 스크립팅** — `man bash`, "Bash Pitfalls" (mywiki.wooledge.org)
- **운영 자동화** — Ansible, Terraform
- **컨테이너** — docker, podman, k8s
- **관측** — prometheus, loki, grafana
- **보안** — STIG, CIS Benchmarks

처음부터 끝까지 인덱스: 책 앞부분의 *통합 목차* 참고.

\newpage

---


# 부록 — 주제별 빠른 찾기

| 하고 싶은 일 | 가야 할 장 |
|-------------|-------------|
| 패스워드 없이 로그인 | 제2장 SSH 키와 에이전트 |
| 베스천 너머 호스트 접속 | 제3장 SSH 고급 (ProxyJump) |
| 여러 서버에 같은 명령 | 제4장 SSH 자동화 |
| 매일 백업 자동화 | 제7장 rsync + 제25장 cron |
| 끊겨도 살아있는 작업 | 제26장 screen/tmux 또는 제27장 nohup |
| 디스크 어디가 가득 찼나 | 제41장 df/du + 제28장 lsof (`+L1`) |
| 포트 누가 점유? | 제30장 ss / 제28장 lsof |
| 이 호스트 살아있나 | 제31장 ping / 제33장 nc |
| 패킷 진짜 흐름 보기 | 제34장 tcpdump |
| HTTPS 인증서 만료일 | 제40장 openssl (s_client) |
| 사용자에게 좁은 권한만 | 제39장 sudo (NOPASSWD) + 제2장 (`command=`) |
| 큰 파일 ssh 로 보내기 | 제7장 rsync (`-avzP`) |
| FTP 서버에 매일 업로드 | 제9장 FTP 자동화 |
| 파일 권한 사고 회복 | 제37장 chmod/chown |
| 서비스 만들기 | 제23장 systemd |
| 부팅 왜 느리지 | 제23장 systemd (`systemd-analyze`) |
| 어제 로그 보기 | 제24장 journalctl (`--since yesterday`) |
| USB 부팅 디스크 굽기 | 제42장 dd |
| 패키지 어디서 왔나 | 제43장 apt / 제44장 dnf |
| 셸 별칭/PATH 정리 | 제47장 history/alias/env |

\newpage

# 부록 — 만든 사람의 말

이 책은 옵시디언 위키 안에서 챕터 단위로 작성한 후 단권으로 묶었다. 원본 챕터들은 다음 위치에 그대로 보존되어 있다.

```
인프라/Linux 핸드북/
├── 00_INDEX.md
├── 01_SSH.md
├── 02_SSH_키와_에이전트.md
├── ...
└── 48_man_info_apropos.md
```

각 챕터 단위로 옵시디언에서 위키링크를 따라가며 읽기에 가장 편리하다. 단권본은 PDF/EPUB 출판을 위한 통합 형태다.

Pandoc 변환 예:

```bash
pandoc Linux_명령어_핸드북.md -o handbook.pdf \
  --pdf-engine=xelatex \
  --toc --toc-depth=2 \
  -V geometry:margin=2cm \
  -V mainfont="Noto Sans CJK KR" \
  -V monofont="Noto Sans Mono CJK KR"

pandoc Linux_명령어_핸드북.md -o handbook.epub \
  --toc --toc-depth=2 \
  --metadata title="Linux 명령어 핸드북"
```

이 책의 모든 내용은 자유롭게 사용·수정·재배포할 수 있다.
