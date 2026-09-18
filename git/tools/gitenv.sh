# gitenv.sh — 진짜 git 을 결정론적으로 돌리는 환경 (PLAN.md §0.9)
#
#   GITENV_SCRATCH=<scratch 디렉터리> . tools/gitenv.sh
#
# 디렉터리를 인자가 아니라 변수로 받는 까닭: POSIX sh(dash)의 '.' 은
# 뒤에 붙인 인자를 넘기지 않는다. bash 에서만 되는 꼴로 쓰면 안 된다.
#
# 모든 실험(run_all.py)과 픽스처 생성(tools/make_golden.py)이 이 파일을
# 읽고 나서 git 을 부른다. 목적은 하나 — 세 번 돌려 캡처가 바이트까지
# 같게 하는 것. 커밋 id 는 작성자·시각·시간대까지 해시에 들어가므로,
# 이 가운데 하나만 새어 들어와도 덱의 모든 id 가 매번 달라진다.
#
# 왜 이것들인가:
#   GIT_CONFIG_GLOBAL=/dev/null
#       이 기계의 ~/.gitconfig 에는 safe.directory=* 와
#       credential.helper=store 가 있다. 캡처에 새면 독자의 화면과
#       다르다.
#   GIT_CONFIG_NOSYSTEM=1   /etc/gitconfig 도 읽지 않는다.
#   HOME=<scratch>          ~ 아래 무엇도(자격 증명 파일 포함) 안 읽게.
#   *_DATE=1700000000 +0900
#       고정 시각. 2023-11-14 22:13:20 UTC 이고, +0900 은 독자가
#       한국 시간대로 읽게 둔 것.
#   TZ=UTC LANG=C LC_ALL=C  날짜 표시와 메시지가 기계마다 안 바뀌게.
#   GIT_PAGER=cat PAGER=cat --no-pager 를 잊어도 멈추지 않게.
#   GIT_TERMINAL_PROMPT=0   자격 증명을 묻느라 멈추는 일이 없게.
#   GIT_ADVICE=0            "hint:" 조언 줄은 버전마다 문구가 바뀐다.
#
# init.defaultBranch 는 환경 변수가 없어 여기서 못 박지 못한다.
# run_all.py 가 git init 마다 -b main 을 붙인다(§0.9).
# 팩 결정론(pack.threads=1·window=10·depth=50)은 저장소 설정이라
# 역시 실험마다 git config 로 넣고, 슬라이드 캡션에 그 값을 적는다.
#
# 이 파일은 sh 로 source 된다. bash 전용 문법을 쓰지 말 것.

if [ -z "${GITENV_SCRATCH:-}" ]; then
  echo 'gitenv.sh: GITENV_SCRATCH 에 scratch 디렉터리를 줄 것' >&2
  return 2 2>/dev/null || exit 2
fi

mkdir -p "$GITENV_SCRATCH"

export HOME="$GITENV_SCRATCH"
export GIT_CONFIG_GLOBAL=/dev/null
export GIT_CONFIG_NOSYSTEM=1
export GIT_AUTHOR_NAME='A U Thor'
export GIT_AUTHOR_EMAIL='author@example.com'
export GIT_AUTHOR_DATE='1700000000 +0900'
export GIT_COMMITTER_NAME='C O Mitter'
export GIT_COMMITTER_EMAIL='committer@example.com'
export GIT_COMMITTER_DATE='1700000000 +0900'
export TZ=UTC
export LANG=C
export LC_ALL=C
export GIT_PAGER=cat
export PAGER=cat
export GIT_TERMINAL_PROMPT=0
export GIT_ADVICE=0
export EDITOR=true
export GIT_EDITOR=true
unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_OBJECT_DIRECTORY
unset GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_TRACE GIT_TRACE_PACKET
