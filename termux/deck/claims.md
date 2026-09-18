# 주장 대장 — 이 덱이 적는 모든 사실의 출처

> **규칙: 슬라이드에 적기 전에 여기 먼저 적는다.** (PLAN.md §0.3)
>
> 날짜·버전 번호·안드로이드 판별 동작·정책 사건(Play 스토어 동결, F-Droid,
> targetSdk 변경, 팬텀 프로세스 한도)·저장소 사실·사람 — Termux 이야기는
> "다들 아는" 주장이 판 하나나 해 하나씩 어긋나 있는 경우가 많다. 기억으로
> 적을 수 있을 것 같은 것일수록 반드시 틀린다.
>
> 출처의 우선순위 (위가 강하다):
>
> 1. upstream 소스나 커밋 그 자체 — `sources/<저장소>@<sha>` 를
>    `<!--SRC-->` 배지로 인용한다(PLAN.md §3.2).
> 2. upstream 문서를 글로 받은 것 — wiki.termux.com, termux-packages
>    GitHub 위키, termux-app·termux-api·termux-exec README,
>    agnostic-apollo 의 Android-Docs.
> 3. 안드로이드 개발자 문서(AOSP 소스나 developer.android.com) — OS 동작.
> 4. GitHub 이슈·릴리스 페이지 — **번호·태그로.**
> 5. 뉴스·블로그 — 커뮤니티 역사에만, 날짜와 함께.
>
> 근거를 못 찾은 문장은 둘 중 하나다: 빼거나,
> 슬라이드에 `<span class="unv">미확인</span>` 을 붙여 모른다고 적는다.
>
> **지식 기준일 규율** — 2025년 이후의 일(최신 릴리스, Play 스토어 판 상태,
> Android 15/16 동작, glibc 패키지, termux-x11 상태)은 만들 때 가져오기나
> WebSearch 로 다시 확인하고 본문에 "2026-09 기준" 을 박는다.
> `check_claims.py` 가 같은 장에 도장이 없으면 빌드를 멈춘다. (PLAN.md §0.4)

## 적는 꼴

한 줄에 주장 하나. 칸은 넷이다.

```
| 주장 | 출처 | 어떻게 확인했나 | 확인한 날 |
```

- **주장** — 슬라이드에 적힐 문장 그대로. "대략", "약" 같은 말을 빼고 수를 적는다.
- **출처** — `저장소@sha7:경로:줄`, 문서 URL(+리비전 id), 이슈 번호 중 가장 강한 것.
- **어떻게 확인했나** — `git show <sha>:<경로> 12–30행` · `wiki revid 1234 본문`
  · `out/dpkg_stats.txt 캡처` 처럼, 다음 사람이 되짚을 수 있게.
- **확인한 날** — YYYY-MM-DD. 빠르게 바뀌는 사실은 이 날짜가 곧 유효기간이다.

`deck/check_claims.py` 가 조각 산문에 적힌 네 자리 연도를 전부 훑어,
이 파일이나 `data/*.tsv` 에 없으면 빌드를 멈춘다. 연도처럼 보이지만
연도가 아닌 수는 `deck/years_ok.txt` 에 적는다.

## 확인해야 할 함정 (PLAN.md §3.1 — 아직 어느 것도 주장이 아니다)

아래는 "틀리기 쉬운 자리" 의 목록일 뿐이다. 3단계에서 출처를 붙여 위의
꼴로 옮기거나 미확인으로 남긴다. 이 목록의 문장을 그대로 슬라이드에
옮기지 말 것.

- 누가 언제 시작했나 — 첫 커밋 날짜는 GitHub API 의 커밋 목록 끝에서.
- 터미널 에뮬레이터의 계보 — `terminal-emulator/` 머리 주석의 저작권 표시.
- Play 스토어 판이 오래 멈춘 까닭 — Android 10(API 29)의 앱 데이터 실행
  제한과 targetSdk 의 관계. `Termux-and-Android-10` 위키와 이슈 번호로.
- F-Droid 배포 주기와 서명 키를 누가 가졌나 — README 의 해당 줄.
- `sharedUserId` 와 "같은 키로 서명" 규칙 — 매니페스트와 README.
- 팬텀 프로세스 한도(Android 12+)의 수와 범위 — README · 이슈 · Android-Docs,
  `settings_enable_monitor_phantom_procs` 우회. 이 기기의 값은 data/device.txt.
- termux-exec 의 시스템 링커 실행 방식 — 소스와 설치된 파일 이름.
- 부트스트랩 zip 을 누가 어디서 만들어 APK 에 싣나 — `TermuxInstaller` 와 CI.
- glibc 패키지의 이름 규칙과 러너 — 저장소에서 확인.
- 저장소 계층 main/x11/root 와 TUR — `tur-repo` 패키지, 이 기기의 sources.list.
- termux-app 판마다 요구하는 최소 안드로이드 — 태그마다 `minSdkVersion`.
- 최신 릴리스와 날짜 — `data/releases.tsv` 에서만 인용한다.

## 주장

| 주장 | 출처 | 어떻게 확인했나 | 확인한 날 |
|---|---|---|---|
| termux-app 저장소의 첫 커밋은 2015-10-25 (Initial commit) | git termux-app a18ee58 | `git log --reverse` 첫 줄의 작성 날짜 | 2026-09-18 |
| termux-packages 저장소의 첫 커밋은 2015-06-12 | git termux-packages a730abe6e | `git log --reverse` | 2026-09-18 |
| termux-api 저장소의 첫 커밋은 2015-07-03 | git termux-api 9e043ef | `git log --reverse` | 2026-09-18 |
| 여러 저장소의 첫 커밋 작성자는 Fredrik Fornwall 이다(termux-app·packages·api·widget·styling·tasker·boot·float·exec·api-package) | git 첫 커밋 메타데이터 | `git log --reverse --format=%an` | 2026-09-18 |
| 첫 GitHub 릴리스는 v0.17 (2015-10-25) | data/releases.tsv | gh_api releases termux/termux-app | 2026-09-18 |
| 최신 안정판은 v0.118.3 (릴리스 날짜 2025-05-22, 2026-09 기준) | data/releases.tsv · readme-termux-app 1.3 "Latest version is v0.118.3" | API 와 README 두 곳이 같다 | 2026-09-18 |
| 최신 사전 릴리스는 v0.119.0-beta.3 (2025-05-22, 2026-09 기준) | data/releases.tsv | gh_api | 2026-09-18 |
| targetSdk 는 v0.66 태그(2019-01-21)부터 28 이다 | data/app_sdk.tsv | 태그 95개의 app/build.gradle | 2026-09-18 |
| minSdk 는 v0.76 태그(2019-10-20)에서 21 → 24 로 바뀌었다 | data/app_sdk.tsv | git show v0.75/v0.76:app/build.gradle | 2026-09-18 |
| README 는 Android 5·6 지원 종료를 "2020-01-01 v0.83" 으로 적는다 (저장소에 v0.83 태그는 없다) | readme-termux-app 1.3 · `git tag` | README 문장 + 태그 목록 대조 | 2026-09-18 |
| Android 5·6 용 앱은 2022-05-24 GitHub 빌드로 다시 나왔으나 패키지 갱신은 없다 (PR #2740) | readme-termux-app 1.3 | README 문장, PR #2740 은 2022-04-26 개설·2022-05-23 닫힘 | 2026-09-18 |
| 앱과 패키지를 온전히 지원하는 것은 Android 7 이상 | readme-termux-app 1.3 | README 문장 | 2026-09-18 |
| Termux 앱과 플러그인은 sharedUserId com.termux 를 쓰므로 같은 키로 서명된 것끼리만 함께 쓸 수 있고, 설치처를 섞으면 안 된다 | readme-termux-app 1.3 | README 문장 | 2026-09-18 |
| F-Droid 판은 F-Droid 가 빌드·서명하며 메인테이너는 그 서명 키를 갖고 있지 않다 | readme-termux-app 1.3.1 | README 문장 | 2026-09-18 |
| GitHub 판 APK 는 공개된 테스트 키(testkey_untrusted.jks)로 서명된다 | readme-termux-app 1.3.2 | README 문장 | 2026-09-18 |
| F-Droid 판은 유니버설 APK 하나만 낸다. APK+부트스트랩 설치 크기는 약 180MB | readme-termux-app 1.3.1 | README 문장 | 2026-09-18 |
| Google Play 판은 Android 11+ 용이며 별도 저장소(termux-play-store)에서 빌드되고 sharedUserId 가 없다 | readme-termux-app 1.3.3 | README 문장 | 2026-09-18 |
| Termux 는 2024년 6월부터 Google Play 에 다시 올라왔다 | wiki-termux-google-play revid 6569 | 위키 문장 | 2026-09-18 |
| 옛 Google Play 판의 마지막 판은 v0.101 이다 | post-2022-02-15 (termux.github.io) | 공지 문장 "latest version v0.101" | 2026-09-18 |
| Play 판 폐지 경고 배너는 termux-tools v0.135 (termux-packages PR #7493, 2021-09-08 개설) | post-2022-02-15 · GitHub API issues/7493 | 공지 문장 + API | 2026-09-18 |
| 2022-02-15 취약점 공개는 v0.118.0 릴리스 30일 뒤였다 | post-2022-02-15 | 공지 문장 | 2026-09-18 |
| Google 은 targetSdk 29 이상을 요구하지만 Termux 는 W^X 제한 때문에 28 을 쓴다 | gh-packages-termux-and-android-10 1 | 위키 문장 | 2026-09-18 |
| targetSdk 29 이상 앱은 앱 홈 디렉터리 파일에 execve() 를 부를 수 없다 | dev-android-10-behavior 1.3 | 개발자 문서 문장 | 2026-09-18 |
| 관련 이슈: #1072 (2019-03-18 개설), #2155 (2021-07-03 개설) | GitHub API issues | API created_at | 2026-09-18 |
| Android 12+ 는 팬텀 프로세스를 모든 앱 합쳐 32개 넘게 두지 않고, CPU 를 과하게 쓰는 프로세스도 죽인다 | readme-termux-app 1 (NOTICE) · android-docs-phantom 2 | 두 문서 | 2026-09-18 |
| 팬텀 프로세스 이슈 #2366 은 2021-10-29 에 열렸다 | GitHub API issues/2366 | API | 2026-09-18 |
| Android 12L·13+ 는 settings put global settings_enable_monitor_phantom_procs false 로 두 킬러를 끈다(adb·루트) | android-docs-phantom 2.9.2 | 문서 명령 | 2026-09-18 |
| Android 14+ 는 개발자 옵션 "Disable child process restrictions" 토글이 있다 | android-docs-phantom 2.9.1 | 문서 문장 | 2026-09-18 |
| Android 12 에는 CPU 킬러를 끄는 설정이 없다 | android-docs-phantom 2.8.3 | 문서 문장 | 2026-09-18 |
| Android 14 이상에서 am 명령은 root·shell 만 실행할 수 있다 | gh-packages-termux-execution-environment 1.4.1 | 위키 문장 | 2026-09-18 |
| Termux 는 에뮬레이션·컨테이너 없이 안드로이드 커널 위에서 NDK 로 컴파일한 프로그램을 그대로 돌린다 | gh-packages-termux-execution-environment 1.1 · wiki-getting-started 1 | 두 문서 | 2026-09-18 |
| 접두사 $PREFIX 는 /data/data/com.termux/files/usr, $HOME 은 /data/data/com.termux/files/home 이며 SD 카드로 옮길 수 없다(권한·심볼릭 링크 필요, 경로가 바이너리에 박힘) | wiki-getting-started 1 | 위키 문장 | 2026-09-18 |
| 공유 저장소(/sdcard)는 noexec 로 마운트되고 심볼릭 링크를 만들 수 없으며 이름의 대소문자를 가리지 않는다 | gh-packages-termux-execution-environment 1.3.1 | 위키 문장 | 2026-09-18 |
| 부트스트랩은 앱에 실려 오는 최소 패키지 묶음이며 zip 은 termux-packages 릴리스로 빌드된다 | readme-termux-app 1.3 | README 문장 | 2026-09-18 |
| 기본 저장소는 packages.termux.dev/apt/termux-main (stable main), CDN 은 packages-cf.termux.dev | gh-packages-mirrors 2.2 | 위키 표 | 2026-09-18 |
| TUR 은 2022-07-02 termux-packages 를 포크해 시작했다 | git tur a1c3f7f | 첫 커밋 제목 | 2026-09-18 |
| termux/glibc-packages 의 첫 커밋은 2023-09-30 | git glibc-packages e8b1d40 | 첫 커밋 | 2026-09-18 |
| proot-distro 첫 커밋은 2020-07-20 | git proot-distro a2f61aa | 첫 커밋 | 2026-09-18 |
| termux-exec 첫 커밋은 2017-09-17 | git termux-exec 8b09741 | 첫 커밋 | 2026-09-18 |
| termux-x11 첫 커밋은 2019-06-26 | git termux-x11 5b4bf8e | 첫 커밋 | 2026-09-18 |
| termux-tools 는 2022-07-18 독립 저장소로 시작했다 | git termux-tools acad033 | 첫 커밋 | 2026-09-18 |
| wiki.termux.com 의 첫 리비전은 2017-07-04 (Main Page, revid 1) | wiki API rvdir=newer | API 응답 | 2026-09-18 |
| 2024-11-11 NLnet NGI Mobifree 보조금 선정 공지 — termux-core 라이브러리·APK Library File·동적 변수 | post-2024-11-11 | 공지 | 2026-09-18 |
| 2025년 6월 GitHub Secure Open Source Fund 2기 참가 | post-2025-08-11 | 공지 | 2026-09-18 |
| 2026-08-31 부터 Google Play 새 앱·업데이트는 API 36 이상 target (2026-09 기준) | dev-android-target-sdk-play | 개발자 문서 | 2026-09-18 |
| sharedUserId 는 API 29 에서 폐지 예정이 되었고, sharedUserMaxSdkVersion 은 API 33 에 생겼다 | dev-android-manifest-element | 개발자 문서 | 2026-09-18 |
| Android 판 ↔ API 수준: 5.0=21 · 6.0=23 · 7.0=24 · 9=28 · 10=29 · 11=30 · 12=31 · 12L=32 · 13=33 · 14=34 · 15=35 · 16=36 | dev-android-platforms | 개발자 문서 목록 | 2026-09-18 |
| 앱 아이콘은 검정 화면·회색(#BFCBCD) 테두리·흰 블록 커서다(초록 없음) | termux-app@084d709 art/ic_launcher.svg | 파일 내용 | 2026-09-18 |
| 터미널 기본 16색은 TerminalColorScheme.java 의 DEFAULT_COLORSCHEME 에 있다 | termux-app@084d709 terminal-emulator/…/TerminalColorScheme.java | 파일 내용 | 2026-09-18 |
| 안드로이드는 앱마다 고유한 uid 를 주고 제 프로세스에서 돌려, 커널 수준의 앱 샌드박스를 만든다 | aosp-app-sandbox 1 | 문서 문장 | 2026-09-18 |
| 샌드박스를 깨려면 대개 리눅스 커널을 뚫어야 한다(심층 방어가 필요) | aosp-app-sandbox 1.1 | 문서 문장 | 2026-09-18 |
| 안드로이드는 SELinux 를 enforcing 모드로 쓰며, root 권한 프로세스도 MAC 의 대상이다 | aosp-selinux 1 | 문서 문장 | 2026-09-18 |
| Android O(8.0) 부터 zygote 에 seccomp 필터 하나를 걸어 모든 앱에 적용한다 | aosp-seccomp 2 | 블로그 문장 | 2026-09-18 |
| Zygote 는 같은 ABI 의 모든 시스템·앱 프로세스의 뿌리이며 init 이 띄운다 | aosp-zygote 1 | 문서 문장 | 2026-09-18 |
| 앱 전용 내부 저장소는 다른 앱이 못 읽고, 앱을 지우면 함께 지워진다 | dev-android-app-data 1 | 문서 문장 | 2026-09-18 |
| AID_ROOT 0 · AID_SYSTEM 1000 · AID_EXTERNAL_STORAGE 1077 · AID_SHELL 2000 · AID_INET 3003(AF_INET 소켓을 만들 수 있다) · AID_EVERYBODY 9997 · AID_APP_START 10000 · AID_CACHE_GID_START 20000 · AID_SHARED_GID_START 50000 · AID_USER_OFFSET 100000 | aosp-fs-config | 헤더의 #define 줄 | 2026-09-18 |
| bionic 은 앱 uid 를 u0_a1234 꼴로 이름 짓는다(AID_APP_START + 1234), 캐시 gid 는 u0_a1234_cache, 공유 gid 는 all_a1234 | aosp-bionic-grp-pwd | 소스 주석 240–246 행(문서 변환본) | 2026-09-18 |
| Termux 는 FHS 를 따르지 않아 /bin·/etc·/usr·/tmp 가 제자리에 없고, 그래서 데비안·우분투 패키지를 그대로 쓰지 않는다 | wiki-differences-from-linux 1 | 위키 문장 | 2026-09-18 |
| Android 7 이상에서는 LD_LIBRARY_PATH 대신 ELF 의 DT_RUNPATH 를 쓴다 | wiki-differences-from-linux 1 | 위키 문장 | 2026-09-18 |
| 모든 패키지는 NDK 로 컴파일되어 시스템의 bionic(/system/lib64 의 libc.so·libm.so·libdl.so)에 링크된다 | wiki-differences-from-linux 2 | 위키 문장 | 2026-09-18 |
| 리눅스 배포판의 동적 링크 프로그램은 링커 경로(/lib)가 없고 libc ABI 가 달라 돌지 않는다 | wiki-differences-from-linux 2 | 위키 문장 | 2026-09-18 |
| 루트 파일시스템과 홈은 /data 파티션의 앱 데이터에 있고, 앱을 지우거나 데이터를 지우면 함께 사라진다 | wiki-differences-from-linux 3 | 위키 문장 | 2026-09-18 |
| Termux 는 단일 사용자다. 모든 것이 앱의 uid 로 돌고 사용자 이름은 uid 에서 나온다 | wiki-differences-from-linux 4 | 위키 문장 | 2026-09-18 |
| 서버 패키지의 기본 포트를 바꿨다: ftpd 8021 · httpd 8080 · sshd 8022 | wiki-differences-from-linux 4 | 위키 문장 | 2026-09-18 |
| Termux 앱은 com.termux 라는 이름의 주 프로세스 하나로 뜨고, 세션·작업은 그 프로세스에서 fork 한 자식이다 | gh-packages-termux-execution-environment 1.2 | 위키 문장 | 2026-09-18 |
| /system/bin 의 파일은 DAC·SELinux 문맥·호출자 검사 때문에 앱이 다 실행할 수는 없다 | gh-packages-termux-execution-environment 1.4.1 | 위키 문장 | 2026-09-18 |
| Termux 의 NDK 헤더 패치(ndk-patches/29/pwd.h.patch)는 getpwuid 를 인라인 함수로 덮어써 집을 $HOME, 셸을 $PREFIX/bin/login 으로 바꾼다 | termux-packages@7d5b4d3 ndk-patches/29/pwd.h.patch 15–58행 | git show | 2026-09-18 |
| 이 기기의 proot 안에서 id 는 uid=0(root) 이지만 보조 그룹에는 1077·3003·9997·20123(u0_a123_cache)·50123(all_a123) 이 남는다 | out/env_termux.txt 2절 | 캡처 | 2026-09-18 |
| libandroid-support: "Library extending the Android C library (Bionic) for additional multibyte, locale and math support" | termux-packages@7d5b4d3 packages/libandroid-support/build.sh TERMUX_PKG_DESCRIPTION | git show | 2026-09-18 |
| libandroid-selinux: "Android fork of libselinux, an SELinux userland library" | termux-packages@7d5b4d3 packages/libandroid-selinux/build.sh | git show | 2026-09-18 |
| 이 기기의 Termux clang 은 __ANDROID_API__ 24 로 짓는다 | out/exp_bionic.txt 2절 | 캡처 | 2026-09-18 |
| Termux 의 bash·ls·termux-api 는 interp /system/bin/linker64, RUNPATH $PREFIX/lib; 우분투 bash 는 /lib/ld-linux-aarch64.so.1 | out/linker_termux.txt · out/linker_proot.txt | 캡처(py/elf.py) | 2026-09-18 |
| 안드로이드의 / 는 요즘 판에서 마운트된 system 파티션이며, /bin → /system/bin, /etc → /system/etc 링크다 | gh-packages-termux-file-system-layout 1.2.1 | 위키 표 | 2026-09-18 |
| /proc 는 보통 hidepid=2 로 마운트되고, /proc/net 은 Android 10 부터 개인정보 때문에 막혔다 | gh-packages-termux-file-system-layout 1.2.1 | 위키 표 | 2026-09-18 |
| /system/bin 을 PATH 에 넣지 말라(Termux 도구와 충돌) — 대체 경로로만 예외 | gh-packages-termux-file-system-layout 1.2.1 | 위키 표 | 2026-09-18 |
| /system/bin 의 핵심 유틸리티는 주로 toybox 가 준다 | gh-packages-termux-file-system-layout 1.2.1.1 | 위키 문장 | 2026-09-18 |
| Android 14 에는 SELinux 파일 문맥 형식이 92개쯤 있다 | gh-packages-termux-execution-environment 1.4.1 | 위키 문장 | 2026-09-18 |
| 루트가 아닌 Android 8 이상에서는 seccomp 필터 때문에 정적 링크 프로그램이 돌지 않을 수 있다 | wiki-differences-from-linux 2 | 위키 문장 | 2026-09-18 |
| android.permission.INTERNET 은 gid inet 에 대응한다 | aosp-platform-xml 52–54행 | 문서 변환본 | 2026-09-18 |
| termux-app 매니페스트는 INTERNET·저장소·WAKE_LOCK·FOREGROUND_SERVICE·RECEIVE_BOOT_COMPLETED 등 17개 권한을 적고, sharedUserId 와 requestLegacyExternalStorage="true" 를 둔다 | termux-app@084d709 app/src/main/AndroidManifest.xml 5·22–38·46행 | out/src_manifest.txt | 2026-09-18 |
| Termux 는 세션(TermuxSession)에 execvp, 백그라운드 작업(TermuxTask)에 Runtime.exec() 를 쓴다 | gh-packages-termux-execution-environment 1.2 | 위키 문장 | 2026-09-18 |
| sshd·crond 처럼 스스로 데몬이 되는 프로그램은 부모가 init(pid 1)이 되어 앱 프로세스에서 떨어지고, 더 쉽게 죽는다 | gh-packages-termux-execution-environment 1.2.3 | 위키 문장 | 2026-09-18 |
| 안드로이드 권한은 설치 때 주는 것(일반·서명), 실행 중 묻는 것(런타임), 특별 권한으로 나뉜다 | dev-android-permissions 1.2 | 문서 절 제목·문장 | 2026-09-18 |
| Android 11 에서 모든 파일 접근(MANAGE_EXTERNAL_STORAGE)을 선언하면 Google Play 출시에 영향이 있을 수 있다 | dev-android-11-storage 1.8 | 문서 문장 | 2026-09-18 |
| 이 기기의 /storage/emulated 는 fuse 로, noexec·nosuid·nodev 로 마운트돼 있다 | out/storage.txt 2절 | 캡처(/proc/mounts) | 2026-09-18 |
| termux-setup-storage 가 만든 ~/storage 링크는 shared·dcim·downloads·documents·movies·music·pictures·podcasts·audiobooks·external-0·media-0 이다(이 기기) | out/storage.txt 1절 | 캡처 | 2026-09-18 |
| Termux 경로: /data/data/com.termux(앱 데이터) · …/termux(프로젝트) · …/files(루트) · …/files/home · …/files/usr(접두사) · …/cache(캐시) | gh-packages-termux-file-system-layout 1.3 | 위키 표 | 2026-09-18 |
| 앱 uid = user_id × 100000 + 10000 + app_id (예: 0 → 10160/u0_a160, 10 → 1010160/u10_a160); 보조 사용자·프로필 id 는 10 부터 | gh-packages-termux-file-system-layout 1.3.1 | 위키 문장 | 2026-09-18 |
| Termux 앱은 주 사용자(0)에만 설치할 수 있다(패키지가 /data/data/com.termux 를 전제로 지어진다) | gh-packages-termux-file-system-layout 1.3.1 | 위키 문장 | 2026-09-18 |
| 앱 데이터는 uid DAC · SELinux MCS · targetSdk 30 이상의 격리, 세 겹으로 지켜진다 | gh-packages-termux-file-system-layout 1.3.1 | 위키 목록 | 2026-09-18 |
| 앱 데이터를 남이 볼 길: 같은 키·같은 sharedUserId 의 앱, SAF 로 사용자가 허락, RUN_COMMAND 같은 API | gh-packages-termux-file-system-layout 1.3.1 | 위키 목록 | 2026-09-18 |
| Android 8.1 이하에는 /bin 이 없고, 9 이상에서는 /bin 이 /system/bin 링크이며, /usr 는 어느 판에도 없다 | termux-exec-technical 1.2.1 | 문서 문장 | 2026-09-18 |
| termux-exec 는 exec() 계열을 가로채 /bin/*·/usr/bin/* 경로와 셔뱅의 해석기 경로를 $TERMUX__PREFIX/bin/ 로 바꾼다 | termux-exec-technical 1.2.1.1 | 문서 문장 | 2026-09-18 |
| LD_PRELOAD 라이브러리는 direct·linker 두 변형이 있고, 주 변형을 $PREFIX/lib/libtermux-exec-ld-preload.so 로 복사해 login 이 LD_PRELOAD 로 내보낸다 | termux-exec-technical 1 · termux-tools@a62f7b2 scripts/login.in 42–54 | 문서 + 소스 | 2026-09-18 |
| Android 10 부터 SELinux 정책이 targetSdk 29 이상 untrusted_app 이 app_data_file 을 exec 하지 못하게 했다(W^X) | termux-exec-technical 1.1.1 | 문서 문장 | 2026-09-18 |
| 시스템 링커 실행: /system/bin/linker64 에 실행 파일 경로를 넘기면 앱 데이터의 파일도 실행된다 — 커널·SELinux 는 링커(system_linker_exec)만 본다. 링커의 이 기능은 Android 10 에 들어갔다 | termux-exec-technical 1.1.1.1 | 문서 문장 | 2026-09-18 |
| 시스템 링커 실행의 문제: LD_PRELOAD 가 모든 입구에 필요, /proc/self/exe 가 링커를 가리킴, 정적 바이너리 불가, execve 직접 호출은 패치 필요, Play 정책과 맞지 않음 | termux-exec-technical 1.1.1.2 | 문서 목록 | 2026-09-18 |
| termux-fix-shebang 은 첫 줄의 #!…/bin/X 나 #!…/sbin/X 를 #!$PREFIX/bin/X 로 sed 로 고쳐 쓴다 | termux-tools@a62f7b2 scripts/termux-fix-shebang.in 11행 | 소스 | 2026-09-18 |
| NDK 헤더 패치 paths.h: _PATH_BSHELL → $PREFIX/bin/sh, _PATH_DEFPATH → $PREFIX/bin, _PATH_TMP → $PREFIX/tmp/ | termux-packages@7d5b4d3 ndk-patches/29/paths.h.patch | 소스 | 2026-09-18 |
| 툴체인 설정은 교차 빌드 때 LDFLAGS 에 -Wl,-rpath=$TERMUX__PREFIX__LIB_DIR 를 더한다 | termux-packages@7d5b4d3 scripts/build/toolchain/termux_setup_toolchain_29.sh 34행 | 소스 | 2026-09-18 |
| termux-core 의 termuxPrefixPath() 는 /bin·/usr/bin 과 /bin/…·/xxx/bin/… 을 접두사의 bin 으로 바꾼다 | termux-core-package@efbbd0d lib/termux-core_nos_c/tre/src/termux/file/TermuxFile.c 283–350 | 소스 | 2026-09-18 |
| 이 기기에 설치된 판: termux-exec 1:2.5.0-1, termux-core 0.4.0-1, termux-tools 1.46.0+really1.45.0-1 | out/pkg_script.txt · dpkg -s (tmx) | 캡처·명령 | 2026-09-18 |
| Android 10 의 sepolicy 는 targetSdk 29 이상 untrusted_app 의 app_data_file execute_no_trans 를 막고, untrusted_app_25(≤25)·untrusted_app_27(26–28) 은 호환을 위해 허용한다 | android-docs-exec-restrictions 1.2.1 (app_neverallows.te·untrusted_app_27.te 인용) | 문서 인용 | 2026-09-18 |
| targetSdk 29 이상 앱도 dlopen()(mmap PROT_EXEC)은 계속 된다 — exec() 만 막힌다 | android-docs-exec-restrictions 1.2.1 | 문서 인용 | 2026-09-18 |
| 이 기기의 Termux 셸의 SELinux 문맥은 u:r:untrusted_app_27 이다 | out/env_termux.txt 6절 | 캡처 | 2026-09-18 |
| TERMUX_EXEC__SYSTEM_LINKER_EXEC__MODE: disable·enable(기본, 필요할 때만)·force; enable 은 Android 10 이상·root/shell 아님·untrusted_app_25/27 아님·앱 데이터 아래 파일일 때만 쓴다 | termux-exec-usage 1.8.1 | 문서 | 2026-09-18 |
| 새 세션의 셸은 $PREFIX/bin 의 login·bash·zsh·fish 중 실행 가능한 첫 파일이다(없거나 안전 모드면 /system/bin/sh) | termux-app@084d709 termux-shared/src/main/java/com/termux/shared/termux/shell/command/runner/terminal/TermuxSession.java 93–114 · UnixShellEnvironment.java 56 | 소스 | 2026-09-18 |
| login 은 $PREFIX/lib/libtermux-exec-ld-preload.so 가 있으면 LD_PRELOAD 로 내보내고, coreutils true 가 실패하면 푼다 | termux-tools@a62f7b2 scripts/login.in 42–54 | 소스 | 2026-09-18 |
| termux-app 은 app·termux-shared·terminal-emulator·terminal-view 네 모듈이다 | termux-app@084d709 settings.gradle | 소스 | 2026-09-18 |
| Termux 의 터미널 처리는 Android Terminal Emulator(jackpal) 에 기반하며 그 Apache-2.0 코드를 쓴다 | termux-app@084d709 README.md 199행 · LICENSE.md 5행 | 소스 | 2026-09-18 |
| TerminalEmulator 는 xterm 의 일부를 흉내 낸다(xterm 은 VT100 의 일부를 흉내) | termux-app@084d709 terminal-emulator/…/TerminalEmulator.java 머리 주석 | 소스 | 2026-09-18 |
| create_subprocess 는 /dev/ptmx 를 열고 grantpt·unlockpt·ptsname_r, IUTF8 켜고 IXON·IXOFF 끄고(Ctrl+S 멈춤 방지), fork·setsid·dup2 로 PTY 를 표준 입출력에 붙인 뒤 execvp 한다 | termux-app@084d709 terminal-emulator/src/main/jni/termux.c 36–113 | 소스 | 2026-09-18 |
| TermuxService 는 포그라운드 서비스이고, 웨이크락으로 PARTIAL_WAKE_LOCK 과 WIFI_MODE_FULL_HIGH_PERF 를 잡고 배터리 최적화 해제를 요청한다 | termux-app@084d709 app/…/TermuxService.java 203–206·303–330 · out/src_app.txt | 소스 | 2026-09-18 |
| 부트스트랩 zip 은 아키텍처별로 .incbin 으로 앱의 네이티브 라이브러리에 박히고, 설치는 SYMLINKS.txt 로 링크를 세운 뒤 스테이징을 접두사로 옮긴다 | termux-app@084d709 app/src/main/cpp/termux-bootstrap-zip.S · TermuxInstaller.java 40–58·207–215 | 소스 | 2026-09-18 |
| RUN_COMMAND 인텐트로 0.95 부터 서드파티 앱이 Termux 문맥에서 명령을 돌릴 수 있고, com.termux.permission.RUN_COMMAND 권한과 allow-external-apps=true 가 둘 다 필요하다 | gh-app-run_command-intent 1·1.2.1·1.2.2 | 위키 | 2026-09-18 |
| termux.properties 키는 TermuxPropertyConstants 에 정의돼 있다(extra-keys·bell-character·terminal-transcript-rows 등) | termux-app@084d709 termux-shared/…/TermuxPropertyConstants.java · out/src_app.txt | 소스 | 2026-09-18 |
| 이 기기의 ~/.termux 에는 termux.properties 하나만 있다 | out/dot_termux.txt | 캡처 | 2026-09-18 |
| 셸을 못 찾거나 안전(failsafe) 세션이면 /system/bin/sh 를 쓴다 | termux-app@084d709 TermuxSession.java 105–114 | 소스 | 2026-09-18 |
| pkg 는 root 로 실행하면 "Error: Cannot run 'pkg' command as root" 로 멈춘다 | termux-tools@a62f7b2 scripts/pkg.in 4–8 | 소스 | 2026-09-18 |
| pkg 는 apt 와 pacman 두 관리자를 다루며, 하위 명령을 접두어로 받아(i*·up|upg*·un*|rem*…) apt 명령으로 바꾼다 | termux-tools@a62f7b2 scripts/pkg.in 409–442 | 소스 | 2026-09-18 |
| pkg install·search 는 미러를 고르고, 캐시가 없거나 sources.list 가 캐시보다 새롭거나 캐시가 1200초보다 오래되면 apt update 를 한다 | termux-tools@a62f7b2 scripts/pkg.in 362–393·102–109·414·420 | 소스 | 2026-09-18 |
| pkg upgrade 는 apt update 뒤 apt full-upgrade 다 | termux-tools@a62f7b2 scripts/pkg.in 423 | 소스 | 2026-09-18 |
| termux-tools 패키지의 판은 1.46.0+really1.45.0 이고 소스는 v1.45.0 태그다(Essential) | termux-packages@7d5b4d3 packages/termux-tools/build.sh | 소스 | 2026-09-18 |
| build-package.sh 는 설정·의존성·소스 받기·툴체인·패치·configure·make·make install·massage·패키지 만들기(debian·pacman) 순으로 termux_step_* 를 부른다 | termux-packages@7d5b4d3 build-package.sh 737–813 | 소스 | 2026-09-18 |
| massage 단계가 첫 줄의 #!…/bin/X 를 #!$TERMUX_PREFIX/bin/X 로 고친다(이미 /system/ 이나 접두사면 건너뜀) | termux-packages@7d5b4d3 scripts/build/termux_step_massage.sh 79–116 | 소스 | 2026-09-18 |
| 부트스트랩은 기본으로 aarch64·arm·i686·x86_64 네 아키텍처, apt(기본)·pacman 두 관리자로 만들 수 있다 | termux-packages@7d5b4d3 scripts/generate-bootstraps.sh 13–37 | 소스 | 2026-09-18 |
| repo.json 은 저장소 채널 셋(packages→termux-main, root-packages→termux-root, x11-packages→termux-x11)을 정한다 | termux-packages@7d5b4d3 repo.json | 소스 | 2026-09-18 |
| 패키지 빌드 요건: root 권한이 필요한 일 금지, 빌드 디렉터리·$TERMUX__PREFIX 밖의 파일 수정 금지, 코딩 지침 준수 | gh-packages-creating-new-package 1.2 | 위키 | 2026-09-18 |
| 기본 저장소 호스팅은 Bintray 가 2021-05-01 에 문을 닫아 Fosshost 로 옮겼다(이슈 #6348) | gh-packages-package-management 1.1 | 위키 | 2026-09-18 |
| Termux 저장소에는 패키지가 1000개가 넘는다 | wiki-getting-started 2 | 위키 | 2026-09-18 |
| 빌드는 공식 Docker 이미지(scripts/run-docker.sh)가 권장이며, 메인테이너와 같은 환경이라 빌드가 재현된다 | gh-packages-build-environment 1.3.1 | 위키 | 2026-09-18 |
| 빌드 시스템은 Termux 앱 안에서도 쓸 수 있지만 모든 패키지가 되지는 않는다(TERMUX_PKG_ON_DEVICE_BUILD_NOT_SUPPORTED). termux-exec 가 안 되는 기기는 지원하지 않고, 기기 빌드 결과는 패키지 관리자가 추적하지 않는다 | gh-packages-build-environment 1.6.1 | 위키 | 2026-09-18 |
| 기본 부트스트랩은 Android 7.0 이상·10 미만과 호환되게 만든다(BOOTSTRAP_ANDROID10_COMPATIBLE=false) | termux-packages@7d5b4d3 scripts/generate-bootstraps.sh 13–15 | 소스 | 2026-09-18 |
| NDK 헤더 패치의 경로가 android-ndk-r28b/toolchains/llvm/prebuilt/linux-x86_64 이다 — 공식 빌드의 호스트가 x86-64 리눅스 | termux-packages@7d5b4d3 ndk-patches/29/pwd.h.patch 1–2 | 소스 | 2026-09-18 |
| massage 단계는 termux_step_strip_elf_symbols 와 termux_step_elf_cleaner 를 부른다 | termux-packages@7d5b4d3 scripts/build/termux_step_massage.sh 58·62 | 소스 | 2026-09-18 |
| 손으로 만든 treasure-hello .deb 는 proot(uid 0) 에서도 dpkg -i 로 설치·dpkg -r 로 제거된다(apt 와 달리 dpkg 에는 root 검사 패치가 없다) | out/deb_by_hand.txt | 캡처 | 2026-09-18 |
| termux-api 는 Android 14(API 34) 미만이면 유닉스 소켓으로 앱에 붙고, 14 이상이면 얼린 앱에서 읽기가 멈추는 문제 때문에 am broadcast 를 쓴다(이슈 #638 댓글) | termux-api-package@9e7f153 termux-api.c 45–85 | 소스 | 2026-09-18 |
| termux-api 는 소켓 상대의 uid 를 SO_PEERCRED 로 확인한다 | termux-api-package@9e7f153 termux-api.c 88–90 | 소스 | 2026-09-18 |
| TermuxApiReceiver 는 메서드 이름으로 45가지 case 를 나눈다 | termux-api@fc26ce1 app/…/TermuxApiReceiver.java · out/src_api.txt 1 | 소스 | 2026-09-18 |
| 이 기기에서 termux-* 84개 중 54개 스크립트가 $PREFIX/libexec/termux-api 를 부른다 | out/api_mechanism.txt 3·4 | 캡처 | 2026-09-18 |
| termux-sms-list 는 threadid·type·read·sender·address·number·received·body·_id 칸을, termux-location 은 latitude·longitude·altitude·accuracy·vertical_accuracy·bearing·speed 칸을 낸다 | termux-api@fc26ce1 SmsInboxAPI.java 250–277 · LocationAPI.java 238–246 | 소스 | 2026-09-18 |
| termux-sms-list 옵션: -d 날짜·-l 개수·-n 번호·-o 건너뛰기·-t 종류(all·inbox·sent·draft·outbox), 출력은 JSON | wiki-termux-sms-list 1.1 | 위키 | 2026-09-18 |
| termux-location 옵션: -p gps·network·passive(기본 gps), -r once·last·updates. GPS 는 건물 안에서 잘 안 되고 기기 시계가 맞아야 한다 | wiki-termux-location 1.1·2 | 위키 | 2026-09-18 |
| tools/tmx.sh 는 개인정보 명령을 실행 전에 거부하고 99 로 끝난다. 시험은 50가지 명령을 넣어 표지 파일이 안 생김을 본다 | out/tmx_deny.txt · tools/tests/test_tmx.py DENIED | 캡처 | 2026-09-18 |
| termux-* 84개의 주인: termux-api 57·termux-tools 13·termux-core 9·termux-exec 2·termux-am-socket 2·proot 1 | out/dpkg_stats.txt 4 | 캡처 | 2026-09-18 |
| Termux:Tasker 0.5+ 는 부르는 앱에 com.termux.permission.RUN_COMMAND 권한이 필수이고, 없으면 FireReceiver 권한 오류가 난다 | readme-termux-tasker 1.6.2 | README | 2026-09-18 |
| ~/.termux/tasker/ 밖의 스크립트를 절대 경로로 부르려면 allow-external-apps=true 가 필요하고, 덜 믿는 앱에 RUN_COMMAND 를 줬다면 켜지 말라(백그라운드에서 임의 명령) | readme-termux-tasker 1.6.3·1.6.4 | README | 2026-09-18 |
| Termux:X11 의 Termux 쪽 패키지는 x11-repo 의 termux-x11-nightly, 앱은 nightly 릴리스 태그로 받는다 | readme-termux-x11 1.4 | README | 2026-09-18 |
| Termux:Boot: 한 번 실행해 부팅 실행을 허락하고, ~/.termux/boot/ 의 스크립트를 이름순으로 돌린다. 먼저 termux-wake-lock 을 권한다 | readme-termux-boot 1.2 | README | 2026-09-18 |
| Termux:Widget: ~/.shortcuts/ 는 전경 세션, ~/.shortcuts/tasks 는 백그라운드 실행. 숨김 디렉터리·깨진 링크·밖을 가리키는 파일은 안 보인다 | readme-termux-widget 1.6.2 | README | 2026-09-18 |
| Termux:Float 은 터미널을 떠 있는 창으로 보이는 플러그인이다 | readme-termux-float 1 | README | 2026-09-18 |
| Termux:Styling: 터미널을 길게 눌러 More… → Style → 색·글꼴 고르기 | readme-termux-styling 1.2 | README | 2026-09-18 |
| Termux:X11 은 NDK 로 지은 완전한 X 서버이고 Android 8 이상, 앱과 termux 패키지 둘 다 필요하다 | readme-termux-x11 1.1·1.4 | README | 2026-09-18 |
