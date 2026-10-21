# 탄막 슈팅 가이드 소스

Node.js 24와 Python 3을 사용합니다. 이 디렉터리에서 `npm ci --ignore-scripts`로 고정된 의존성을 설치하고 `npm run build`로 루트의 `탄막-슈팅-가이드.html`을 만듭니다. 빌드는 작업 중인 `template.html`과 파일 이름순의 `parts/*.html` 조각을 합칩니다.

`npm test`는 먼저 HTML을 새로 빌드하고 모든 Node 테스트를 실행합니다. 코드 영역 추출, V1~V23의 정상·실패 사례, 현재 본문과 실제 산출물의 구조·출처·글꼴을 검사합니다. 각 트랙을 추가할 때 해당 트랙 실행기를 호출하는 테스트도 함께 추가합니다.

`npm run validate`는 V1~V23 전체 검사입니다. 사용자 요청으로 전체 1,500장 하한을 해제했습니다. 빈 덱은 거부하고 2,000장 상한, 코드 출처·실행 검증·오프라인 검사와 등록된 장별 최소 분량은 유지합니다. 앞으로 추가하는 wasm 장의 최소 분량은 내용에 맞춰 정합니다.

빌드할 때마다 `/root/github/treasure_house/tools/embed_mono_font.py`로 고정폭 글꼴을 내장하고, 실제 산출물 검사에서는 같은 도구의 `--check`를 실행합니다. 도구·D2Coding·fontTools·brotli는 기존 환경의 것을 사용합니다. 템플릿의 모든 스크립트는 그대로 보존합니다. 템플릿이 등록한 미사용 `sample` 데모는 보존한 템플릿 등록과 대조해 구분하며, 새 데모에는 등록과 컨테이너 일치를 요구합니다. 템플릿 CSS 설명 주석의 태그 표기는 이스케이프하고 박스 문자는 유니코드 번호로 바꿉니다.

코드 조각은 `data-src`로 `examples/` 아래 파일과 선택한 영역을 가리킵니다. 빌드는 HTML 이스케이프와 들여쓰기 정리를 적용하고 영역 표식을 제거합니다. 출처 없는 블록·없는 파일·없는 영역·30줄 초과·경로 이탈은 오류입니다. 각 트랙 실행기는 검사한 경로를 `examples/<track>/TESTED.txt`에 한 줄씩 기록해야 합니다. 터미널의 빈 `.term` 요소는 `captures/` 아래 실제 출력 파일을 참조하고, 캡처 실행기는 `captures/TESTED.txt`에 검증 경로를 기록합니다.

에셋을 추가할 때는 `examples/assets/LICENSES.md`의 표에 `파일 경로 | 원본 HTTPS URL | 커밋/태그 | SHA-256 | 라이선스 | 라이선스 파일 경로` 순서로 기록합니다. 경로는 `assets/` 기준이며 모든 파일은 에셋 행이나 해당 행이 가리키는 라이선스 파일로 설명되어야 합니다. 허용 식별자는 MIT, BSD-2-Clause, BSD-3-Clause, Apache-2.0, CC0, CC0-1.0입니다.

개발 의존성은 정확한 버전으로 고정했습니다: TypeScript 7.0.2, esbuild 0.28.2, Three.js 0.186.1, @types/three 0.186.0, Playwright 1.64.1. `package-lock.json`도 함께 보관합니다.

`npm run browser:install`은 Chromium을 이 폴더의 `.cache/ms-playwright/`에 설치합니다. Termux Node가 PRoot 안에서도 `android`로 보고하는 경우 Ubuntu ARM64 플랫폼을 명시합니다. 테스트는 `--no-sandbox`와 `--disable-dev-shm-usage`로 실행하며, 브라우저 오류를 무시하거나 테스트를 자동으로 생략하지 않습니다.

`prepare.mjs`는 검사한 공통 예제에서 패턴 뷰어를 esbuild로 번들링합니다. `build.mjs`는 번들을 HTML에 포함하므로 결과 파일을 옮겨도 별도 서버나 스크립트가 필요하지 않습니다. 공통 예제의 테스트는 `foundations.test.mjs`에서 실행하고 검증한 파일을 `examples/foundations/TESTED.txt`에 기록합니다.

pygame 경로는 `bash examples/pygame/commands.sh install`로 `.cache/pygame-venv`에 pygame-ce 2.5.8을 설치합니다. 배포판 이름은 pygame-ce이고 Python 코드에서는 pygame을 불러옵니다. 명령 파일과 Python 테스트는 가상환경이 있으면 그 실행기를 선택합니다. `bash examples/pygame/commands.sh setup`은 창을 잠시 열어 이미지를 그립니다. 자동 검사는 더미 비디오·오디오 드라이버로 같은 코드를 실행합니다.

`npm run capture`는 실제 확인 명령을 실행해 `captures/pygame-setup.txt`와 실행 목록을 갱신합니다. 빌드도 캡처를 먼저 갱신한 뒤 HTML에 넣습니다. Noto Emoji PNG 세 개는 v2.048의 커밋 b3e3051a088047d19fd4d49b1c3ac42fb8c3aaf8로 고정하고 출처·라이선스 원문·SHA-256을 `examples/assets/LICENSES.md`에 기록했습니다.

`bash examples/pygame/commands.sh lv1`로 Lv1을 실행합니다. 방향키/WASD 이동, Z/Space 발사, Shift 집중 이동, Escape 종료입니다. `--headless --frames 1800`을 뒤에 붙이면 같은 폴더의 `replay.json`으로 자동 실행합니다. 각 레벨 폴더는 이미지를 내장하고 라이선스를 포함하므로 폴더만 복사한 뒤 pygame이 설치된 Python으로 `main.py`를 실행할 수도 있습니다.

pygame 단위 테스트는 `examples/pygame/test_snapshots.py`에서 모든 완료 단계의 기준 기록, 렌더링과 폴더 단독 실행을 검사합니다. 새 레벨의 기준 기록은 `examples/pygame/generate_golden.py`로 실제 실행하여 처음 한 번만 생성합니다. 기존 기준 파일은 덮어쓸 수 없습니다.

## pygame 소스 배포와 측정

bash examples/pygame/commands.sh package는 dist/pygame-lv7.zip을 만든다. 소스·JSON·이미지 라이선스·requirements.txt를 포함하고 사용자 최고 점수와 캐시는 제외한다. 압축 해제 뒤 Python 가상환경에 requirements.txt를 설치하고 main.py를 실행한다.

bash examples/pygame/commands.sh diagnose는 실제 버전과 CPU 정보를 출력한다. profile은 cProfile이 켜진 Lv7 자동 재생 1800호출을 측정한다. 파일 읽기·렌더·오디오는 제외하며 게임 오버 뒤 전투가 멈추므로 activeSteps도 확인한다. 화면 프레임 시간이나 다른 트랙과의 직접 순위 비교가 아니다.

## Canvas와 TypeScript

bash examples/canvas-ts/commands.sh version으로 실행기 버전을 확인하고 build로 strict 검사 뒤 dist/canvas-setup.html을 만든다. HTML은 오프라인 파일로 열 수 있다.

PRoot의 Android Node에서는 기본 tsc 실행기 플랫폼이 맞지 않는다. tsc.mjs가 .cache/typescript-linux에 같은 버전7.0.2의 Linux ARM64 패키지만 설치하여 직접 실행한다. 설치 시 플랫폼 제한을 넘기기 위한 --force는 이 격리된 컴파일러 패키지에만 적용하며 설치 스크립트는 실행하지 않는다. 의존성 버전과 루트 node_modules는 변경하지 않는다.

Canvas Lv1~7은 build 뒤 dist/canvas-lvN.html을 열어 조작한다. 최종 단계는 Enter 시작, P 정지/재개, X 폭탄이다. 같은 레벨 이름의 commands.sh 항목은 Node 자동 재생을 출력한다. Lv7은 덱 안의 내장 데모에서도 실행한다.

bash examples/canvas-ts/commands.sh deploy는 최종 HTML을 dist/release/canvas.html로 복사한다. serve는 기본127.0.0.1:8000에서 그 파일만 제공하며 종료는 Ctrl+C다. serve 뒤에0을 붙이면 빈 포트를 선택한다. file URL과 HTTP의 저장소 출처는 다를 수 있다.

profile은 준비2회 뒤 동일 입력1800호출을5회 측정하여 원시 표본과 중앙값을 출력한다. 초기화·렌더·오디오·저장소를 제외하고 프로파일러를 켜지 않는다. pygame의 cProfile 포함 수치와 직접 순위 비교하지 않는다.

## Three.js와 WebGL 검사 환경

Three.js0.186.1과 @types/three0.186.0을 유지한다. bash examples/three-ts/commands.sh build는 strict 검사와 dist/three-setup.html 생성을 수행한다. Three.js MIT 원문은 examples/three-ts/LICENSE-THREE.txt와 배포 번들에 포함한다.

이 PRoot에서 Chromium SwiftShader는 GPU 프로세스 종료 코드6과 CONTEXT_LOST_WEBGL을 반복했다. WebGL 픽셀 검사를 생략하지 않고 Xvfb+Mesa 소프트웨어 OpenGL로 검증한다. 추가한 OS 패키지는 libatk-bridge2.0-0t64, libegl-mesa0, libgl1-mesa-dri, libglx-mesa0, xvfb, xauth이며 Mesa는26.0.8이다. npm 의존성 버전은 바꾸지 않았다.

npm test는 Android Node 환경에서 전용 Xvfb를 띄우고 테스트 뒤 종료한다. 실행기가 SIGINT·SIGTERM·SIGHUP으로 중단돼도 Xvfb와 검사 프로세스 그룹을 함께 끝내며, Xvfb 표준 에러는 처음부터 버린다. PRoot의 Xvfb는 부모가 사라지면 poll 오류를 끝없이 출력해 리다이렉트된 로그를 수십 GB로 키운 적이 있다(`run-tests.test.mjs`가 가짜 Xvfb로 검사). Three 검사만 직접 실행하려면 xvfb-run -a env LIBGL_ALWAYS_SOFTWARE=1 DANMAKU_WEBGL_DRIVER=mesa node --test three.test.mjs를 사용한다. 일반 Linux 환경의 기본 WebGL 검사 경로는 SwiftShader다.

Three 성능 도구는 build 뒤 `bash examples/three-ts/commands.sh profile`로 실행한다. 동일 정적 원 탄환1000개를 개별 Mesh와 InstancedMesh로 그려 경로별 준비2회 뒤5회 표본과 중앙값을 출력한다. 측정 구간은 render와 gl.finish이며 생성·게임 로직·매 프레임 데이터 갱신·브라우저 시작은 제외한다. 드라이버와 브라우저 버전을 함께 기록하며 소프트웨어 렌더러 결과를 실제 GPU나 게임 FPS로 일반화하지 않는다.

T4.8 본문35장은 `parts/48-three-wrap.html`에 있으며 목차와 실제 측정 캡처 `captures/three-profile.txt`를 연결한다. `capture.mjs`는 Three 빌드 뒤 profile 명령으로 캡처를 다시 만든다. Android에서는 이 명령이 Xvfb+Mesa로 실행되어 기존 WebGL 검증과 같은 드라이버 경로를 사용한다.

## C++ wasm 설치 검사 — 첫 조각

`../C++_WASM_테트리스_만들기.html`의 직접 컴파일 방식을 참고한다. Emscripten과 C++ 표준 라이브러리 없이 작은 C ABI 모듈부터 확인한다. 현재 예제는 ABI 버전과 고정 스텝당 위치 더하기만 제공한다.

`bash examples/cpp-wasm/commands.sh build`는 같은 `setup.cpp`를 g++로 빌드해 네이티브 검사를 실행하고, clang++로 wasm32 오브젝트를 만든 뒤 wasm-ld로 링크한다. Node에서 실제 wasm을 인스턴스화하고 도구 버전·실행 결과·바이트 수를 출력한다. 출력은 `dist/wasm-setup.wasm`과 `dist/wasm-setup-native`에 생성된다.

PATH에 g++·clang++·wasm-ld가 필요하며 현재 확인한 wasm 도구는 clang/LLD 21.1.8이다. 경로는 `NATIVE_CXX`, `WASM_CXX`, `WASM_LD`로 각각 지정할 수 있다. C++20·경고 오류 처리·`-ffp-contract=off`를 적용하며 wasm은 프리스탠딩·예외/RTTI 없음·진입점 없음으로 빌드한다.

`node --test wasm.test.mjs`는 정지·양수·음수·소수 이동, 외부 가져오기 부재, 내보내기 목록, 고정128KiB 메모리와 성장 거부, 손상 바이너리와 잘못된 명령 거부를 검사한다. `npm test`에도 포함된다.

빌드가 생성한 `dist/wasm-setup.html`을 브라우저에서 직접 열면 ABI 버전과 계산 결과가 나온다. wasm과 JS를 내장하므로 서버가 필요 없다. Chromium 오프라인 실행·외부 요청 부재·손상 바이트 오류 표시도 검사한다. 설치 본문은 `parts/50-wasm-setup.html`이며 최종 HTML의 5부 목차에서 읽을 수 있다.

메모리 예제는 `node examples/cpp-wasm/memory-build.mjs`로 빌드한다. 같은 `memory.cpp`의 네이티브 검사와 `dist/wasm-memory.wasm` 생성을 수행한다. 좌표4개·16바이트 간격·명시적 초기화·포화 거부를 제공하고 `memory-glue.mjs`가 범위를 검사한 뒤 DataView로 읽는다. `node --test wasm.test.mjs`는 Node와 오프라인 Chromium에서 좌표 읽기까지 확인한다. 본문은 `parts/51-wasm-memory.html`이다.

Lv1은 `node examples/cpp-wasm/lv1/build.mjs`로 네이티브 검사·wasm 빌드·오프라인 HTML 생성을 수행한다. `dist/wasm-lv1.html`을 직접 열고 화면을 클릭한 뒤 방향키·Z/스페이스 발사·Shift 집중 이동으로 조작한다. 화면 포커스를 잃으면 게임 시간이 멈추고 입력을 지운다. `node --test wasm.test.mjs`는 기존 pygame Lv1 기준의60·600·1800스텝을 네이티브/wasm과 비교하고 Chromium에서120화면·이동·발사·픽셀·포커스 정지를 검사한다. 본문20장은 `parts/52-wasm-lv1.html`이다.

Lv2는 `node examples/cpp-wasm/lv2/build.mjs`와 `dist/wasm-lv2.html`을 사용한다. 적은 붉은색, 적탄은 보라색이며 점수·목숨 HUD와 무적 점멸을 제공한다. wasm 검사는 네이티브·Node·Chromium에서 기존 pygame Lv2 기준을 비교하고 오프라인 화면의 적·적탄 픽셀과 조작을 확인한다. 본문22장은 `parts/53-wasm-lv2.html`이다.

Lv3는 `node examples/cpp-wasm/lv3/build.mjs`와 `dist/wasm-lv3.html`을 사용한다. 회전수 사인 다항식·링·조준 부채꼴·나선·파동을 C++로 실행한다. 정수 나눗셈·영벡터 조준·패턴 포화와 세 환경의 기존 기준 일치를 검사한다. 본문16장은 `parts/54-wasm-lv3.html`이다.

Lv4는 `node examples/cpp-wasm/lv4/build.mjs`와 `dist/wasm-lv4.html`을 사용한다. 논리600스텝부터 보스가 등장하며3단계 전환·체력 막대·완료 단계4를 제공한다. 전환 경계와 지연 정리·세 환경 기준 일치·실제 보스/막대 픽셀을 검사한다. 본문20장은 `parts/55-wasm-lv4.html`이다.

Lv5는 `node examples/cpp-wasm/lv5/build.mjs`와 `dist/wasm-lv5.html`을 사용한다. X키 폭탄·그레이즈·파워1~3·아이템·이벤트 알림을 추가했다. 세 환경 기준 기록과 보상 경계·폭탄 유지·HUD를 검사한다. 본문20장은 `parts/56-wasm-lv5.html`이다.

Lv6는 `node examples/cpp-wasm/lv6/build.mjs`와 `dist/wasm-lv6.html`을 사용한다. 같은 JSON을 JS 검증 뒤 C ABI로 전달하며 C++ 커서가 소비한다. 원본 격리·같은 시간 순서·보스 재시도·빈 스테이지·세 환경 기준 일치를 검사한다. 본문16장은 `parts/57-wasm-lv6.html`이다.

Lv7은 `node examples/cpp-wasm/lv7/build.mjs`와 `dist/wasm-lv7.html`을 사용한다. Enter 시작/재시작·P 정지·입자·합성 소리·최고 점수 저장을 제공하며 가이드에도 네 번째 데모로 내장한다. wasm12개 검사는 상태·효과 난수·세 환경 기준 기록·오디오/저장 실패·실제 브라우저 조작을 포함한다. 본문25장은 `parts/58-wasm-lv7.html`, 실제 덱 캡처는 `captures/wasm-lv7.png`다.

메모리를 고려해 `run-tests.mjs`는 테스트 파일을 `--test-concurrency=1`로 순차 실행한다. Linux에서 소프트웨어 WebGL 검사는 `env DANMAKU_WEBGL_DRIVER=mesa LIBGL_ALWAYS_SOFTWARE=1 xvfb-run -a node run-tests.mjs`로 같은 Mesa 경로를 사용할 수 있다.

`node examples/cpp-wasm/inspect.mjs dist/wasm-lv7.wasm --summary`는 실제 내보내기·메모리·ABI 요약을 출력한다. 옵션을 빼면 전체 목록을 보여 준다. 오류 전용 모듈은 `node examples/cpp-wasm/diagnostics-build.mjs`로 빌드하며 게임에 포함하지 않는다. 손상 바이너리·명시적 트랩·범위 밖 읽기를 wasm 검사에서 구분한다. 본문12장은 `parts/59-wasm-debug.html`이다.

부록은 `appendix.mjs`가 `spec/golden/*.json`, 성능 캡처3개, `examples/assets/LICENSES.md`에서 `parts/60-appendix.html`로 생성한다. 루트 빌드가 항상 다시 생성하므로 표를 손으로 수정하지 않는다. 측정 범위가 다른 수치로 성능 순위나 게임 FPS를 주장하지 않으며 wasm 속도 측정값은 없다.

최종 산출물은1301장·내장 데모4개다. Mesa+Xvfb에서 전체 `npm test`140개와 V1~V23을 통과했다. `env DANMAKU_WEBGL_DRIVER=mesa LIBGL_ALWAYS_SOFTWARE=1 xvfb-run -a node capture-deck.mjs`는 표지·코드·도식·목차·네 데모의 오프라인 화면8개를 생성하며 목록은 `captures/DECK-CAPTURES.txt`에 남긴다.
