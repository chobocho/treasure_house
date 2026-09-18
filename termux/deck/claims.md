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
