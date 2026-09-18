#!/bin/sh
# tmx.sh — 이 proot 에서 호스트 Termux 의 유저랜드로 가는 유일한 문.
#
#   sh tools/tmx.sh [--cwd DIR] [--timeout SEC] -- CMD …
#   sh tools/tmx.sh --proot -- CMD …          # proot 쪽에서 돌린다
#   sh tools/tmx.sh --dry-run -- CMD …        # 허용/거부 판정만
#   sh tools/tmx.sh --allow-install -- pkg install -y X
#
# 왜 문이 하나여야 하나: 이 덱은 사용자가 날마다 쓰는 Termux 위에서
# 만들어진다. 캡처 한 줄을 뜨려다 pkg upgrade 가 섞이면 되돌릴 수
# 없다. 그래서 명령을 돌리기 **전에** 거부 목록(PLAN.md §0.7·§0.8)과
# 대조하고, 걸리면 실행하지 않고 99 로 끝낸다.
#
# 거부 목록은 내 실수를 막는 그물이지 샌드박스가 아니다. 변수로 명령
# 이름을 조립하면 빠져나갈 수 있다 — 그런 명령을 쓰지 않는 것이
# 규칙이고, 이 그물은 오타와 복붙을 막는다.
#
# 주의 — Termux 쪽도 proot 의 ptrace 아래에서 돈다. 파일·패키지 DB 는
# 진짜지만 id·uname·/proc/self/status 같은 신원 값은 proot 가 꾸민
# 것이다. 그래서 끝줄의 side=termux 는 "Termux 의 바이너리와 환경으로
# 돌렸다" 는 뜻이고, "네이티브 Termux 에서 돌렸다" 는 뜻이 아니다.
#
# 출력: 명령의 stdout·stderr 를 그대로 흘리고, stdout 의 마지막 줄에
#   ## tmx: side=termux|proot cwd=DIR exit=N
# 을 붙인다. 캡처에 종료 코드가 같이 남아야 슬라이드가 보여 줄 수 있다.
# 종료 코드: 명령의 것 그대로 · 거부 99 · 사용법 오류 2 · 시간 초과 124.

PREFIX_T=/data/data/com.termux/files/usr
HOME_T=/data/data/com.termux/files/home
REPO_T=$HOME_T/github/treasure_house/termux

side=termux
cwd=$(pwd)
tmo=120
dry=0
inst=0
while [ $# -gt 0 ]; do
  case $1 in
    --proot) side=proot ;;
    --cwd) cwd=$2; shift ;;
    --timeout) tmo=$2; shift ;;
    --dry-run) dry=1 ;;
    --allow-install) inst=1 ;;
    --) shift; break ;;
    *) break ;;
  esac
  shift
done
if [ $# -eq 0 ]; then
  echo '사용법: tmx.sh [--proot] [--cwd DIR] [--timeout SEC]' \
       '[--dry-run] [--allow-install] -- CMD …' >&2
  exit 2
fi
cmd=$*

# ── 거부 목록 ──────────────────────────────────────────────────────
# CS 는 "명령이 시작하는 자리" — 줄 머리, ; & | ( ` $( 따옴표 뒤.
# 경로를 붙여 부른 것($PREFIX/bin/termux-reset)도 잡는다.
# 인자로만 나오는 이름(cat …/termux-sms-send)은 거부하지 않는다 —
# 스크립트 본문을 캡처해 보여 주는 장이 있기 때문이다.
CS='(^|[;&|(`'"'"'"]|\$\()[[:space:]]*([^[:space:];&|'"'"'"]*/)?'
END='([[:space:]]|$|[;&|)'"'"'"`])'

# 우리가 만든 시험 패키지만은 지워도 된다(PLAN.md §3.3 deb_by_hand).
# 판정 전에 그 꼴을 빈 명령으로 지워 둔다.
S='[[:space:]]+'
Y="(-y$S)?"
RM1="(apt|apt-get|pkg)$S$Y(remove|purge|uninstall)$S$Y"
RM2="dpkg$S(-r|-P|--remove|--purge)$S"
TH='treasure-hello([[:space:]]|$)'
scan=$(printf '%s' "$cmd" | sed -E \
  -e "s/$RM1$TH/: /g" -e "s/$RM2$TH/: /g")

deny() {
  echo "## tmx: 거부 — $1: $cmd" >&2
  exit 99
}

has() { printf '%s' "$scan" | grep -Eq -- "$1"; }

T='termux-'
has "${CS}${T}(reset|restore|change-repo)${END}" \
  && deny '환경·미러를 바꾼다'
has "${CS}${T}(wifi-enable|telephony-[a-z]+|sms-[a-z]+)${END}" \
  && deny '통신을 건드리거나 개인정보를 읽는다'
has "${CS}${T}(call-log|contact-list|location|camera-photo)${END}" \
  && deny '개인정보를 읽는다(§0.8)'
has "${CS}${T}(microphone-record|notification-list|fingerprint)${END}" \
  && deny '개인정보를 읽는다(§0.8)'
has "${CS}${T}(keystore|nfc|usb)${END}" \
  && deny '개인정보·장치를 건드린다'
has "${CS}${T}(wallpaper|brightness|setup-storage|dialog)${END}" \
  && deny '화면·권한 창을 띄우거나 설정을 바꾼다'
has "${CS}${T}(open|open-url|am)${END}" \
  && deny '다른 앱·인텐트를 띄운다'
has "${CS}${T}volume$S[^-;&|[:space:]]" && deny '음량을 바꾼다'
has "${CS}${T}torch${S}on" && deny '손전등을 켠다'
AM='(start|startservice|start-foreground-service|broadcast'
AM="$AM|force-stop|kill|stopservice|instrument)"
has "${CS}am$S$AM${END}" && deny '앱·인텐트를 띄운다'

# 선택지(-y 따위)가 하위 명령 앞에 와도 잡는다
OPT="(-[^[:space:]]+$S)*"
PKGBAD='(upgrade|up|uninstall|remove|reinstall)'
APTBAD='(upgrade|full-upgrade|dist-upgrade|remove|purge'
APTBAD="$APTBAD|autoremove|autopurge)"
has "${CS}pkg$S$OPT$PKGBAD${END}" && deny '패키지를 올리거나 지운다'
has "${CS}apt(-get)?$S$OPT$APTBAD${END}" \
  && deny '패키지를 올리거나 지운다'
has "${CS}dpkg[^;&|]*[[:space:]](-r|-P|--remove|--purge)${END}" \
  && deny '패키지를 지운다'
if [ $inst -eq 0 ]; then
  has "${CS}pkg$S$OPT(install|in|i|add)${END}" \
    && deny '설치는 --allow-install 로만(§9 결정 5)'
  has "${CS}apt(-get)?$S${OPT}install${END}" \
    && deny '설치는 --allow-install 로만(§9 결정 5)'
  has "${CS}dpkg[^;&|]*[[:space:]](-i|--install)${END}" \
    && deny '설치는 --allow-install 로만(§9 결정 5)'
fi

# 쓰기 동작 — 보호할 곳과 같은 줄에 있으면 거부한다.
WR='(>|[[:space:]]tee([[:space:]]|$)|sed[[:space:]]+-i'
WR="$WR|(^|[[:space:];&|])(cp|mv|rm|ln|touch|mkdir|chmod|truncate)"
WR="$WR[[:space:]])"
if has 'sources\.list' && has "$WR"; then
  deny 'apt 저장소 목록을 고친다'
fi
if has '(~|home|HOME\}?)/\.termux' && has "$WR"; then
  deny '~/.termux 는 사용자 설정이다'
fi

# rm — 재귀 삭제는 scratch/ 나 /tmp/ 아래의 절대 경로만. 재귀가
# 아니어도 $PREFIX·$HOME 을 겨누면 scratch/ 아래만 된다.
# O(명령 길이). awk 로 rm 조각마다 인자를 본다.
bad_rm=$(printf '%s\n' "$scan" | awk -v rep="$REPO_T/scratch" \
  -v rep2="/root/github/treasure_house/termux/scratch" '
  function under(p, d) { return index(p, d "/") == 1 || p == d }
  {
    n = split($0, seg, /[;&|]+/)
    for (s = 1; s <= n; s++) {
      m = split(seg[s], w, /[ \t]+/)
      k = 1
      while (k <= m && w[k] == "") k++
      if (k > m) continue
      c = w[k]; sub(/.*\//, "", c)
      if (c != "rm") continue
      rec = 0; tgt = 0
      for (i = k + 1; i <= m; i++) {
        a = w[i]; gsub(/["\047]/, "", a)
        if (a == "") continue
        if (a ~ /^--recursive$/ || a ~ /^-[a-zA-Z]*[rR]/) {
          rec = 1; continue
        }
        if (a ~ /^-/) continue
        t[++tgt] = a
      }
      for (j = 1; j <= tgt; j++) {
        a = t[j]
        ok = under(a, rep) || under(a, rep2) || index(a, "/tmp/") == 1
        if (rec && !ok) { print a; exit }
        if (!ok && (a ~ /^(~|\$HOME|\$\{HOME\}|\$PREFIX|\$\{PREFIX\})/ \
            || index(a, "/data/data/com.termux/") == 1 \
            || index(a, "/root") == 1)) { print a; exit }
      }
    }
  }')
[ -n "$bad_rm" ] && deny "scratch/ 밖을 지운다($bad_rm)"

if [ $dry -eq 1 ]; then
  echo "## tmx: 허용 — $cmd"
  exit 0
fi

# ── 실행 ───────────────────────────────────────────────────────────
# env -i 로 proot 의 환경(LD_PRELOAD·PROOT_* 따위)을 전부 떼고
# Termux 가 로그인 셸에 주는 것만 다시 세운다. bash 는 --norc 라
# PREFIX·PATH 를 스스로 세우지 않는다(PLAN.md §2 표 3행).
cd "$cwd" || exit 2
if [ $side = termux ]; then
  timeout "$tmo" env -i PREFIX=$PREFIX_T PATH=$PREFIX_T/bin \
    HOME=$HOME_T TMPDIR=$PREFIX_T/tmp LANG=en_US.UTF-8 \
    TERM=xterm-256color DEBIAN_FRONTEND=noninteractive \
    $PREFIX_T/bin/bash --noprofile --norc -c "$cmd"
else
  P=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
  timeout "$tmo" env -i PATH=$P HOME=/root LANG=C.UTF-8 \
    TERM=xterm-256color DEBIAN_FRONTEND=noninteractive \
    /bin/bash --noprofile --norc -c "$cmd"
fi
rc=$?
echo "## tmx: side=$side cwd=$cwd exit=$rc"
exit $rc
