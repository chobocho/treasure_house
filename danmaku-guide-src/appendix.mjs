import { readFileSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
const src = new URL('.', import.meta.url);
const esc = (s) => String(s).replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;');
const table = (head, rows) => `<div class="tblwrap"><table class="kv"><tr>${head.map((s) => `<th>${esc(s)}</th>`).join('')}</tr>${rows.map((row) => `<tr>${row.map((s) => `<td>${esc(s)}</td>`).join('')}</tr>`).join('')}</table></div>`;
const card = (id, title, prose, content = '') => `<article class="card" id="p6-reference-${id}"><h3>${title}</h3><p>${prose}</p>${content}</article>`;

export function renderAppendix() {
  const json = (p) => JSON.parse(readFileSync(new URL(p, src), 'utf8'));
  const py = json('captures/pygame-profile.txt'), canvas = json('captures/canvas-profile.txt'), three = json('captures/three-profile.txt');
  const goldens = Array.from({ length: 7 }, (_, i) => json(`spec/golden/lv${i + 1}.json`));
  const licenseRows = readFileSync(new URL('examples/assets/LICENSES.md', src), 'utf8').split('\n')
    .filter((line) => /^\| noto-emoji\//.test(line)).map((line) => line.split('|').slice(1, -1).map((s) => s.trim()));
  const licenses = `<div class="tblwrap"><table class="kv"><tr><th>파일</th><th>원본</th><th>커밋/태그</th><th>SHA-256</th><th>라이선스</th><th>원문 파일</th></tr>${licenseRows.map(([file, url, revision, digest, license, path]) => {
    if (!url.startsWith('https://') || !/^[a-f0-9]{64}$/.test(digest)) throw new Error('부록 에셋 출처 형식 오류');
    return `<tr><td><code>${esc(file)}</code></td><td><a href="${esc(url)}">원본</a></td><td><code>${esc(revision)}</code></td><td><code>${esc(digest)}</code></td><td>${esc(license)}</td><td><code>assets/${esc(path)}</code></td></tr>`;
  }).join('')}</table></div>`;
  const states = goldens.map((g) => {
    const s = g.checkpoints.at(-1);
    return [`Lv${g.level}`, s.frame, s.bullets, s.enemies, s.score, s.lives, s.phase, s.checksum];
  });
  const methods = [
    ['pygame', py.method, `${py.elapsedMs.toFixed(3)} ms`, `${py.steps}호출 / ${py.activeSteps}전투 스텝`],
    ['Canvas 로직', canvas.method, `${canvas.medianMs.toFixed(3)} ms 중앙값`, `${canvas.samplesMs.length}표본 / ${canvas.steps}호출`],
    ...three.results.map((r) => [`Three ${r.mode}`, three.method, `${r.medianMs.toFixed(3)} ms 중앙값`, `${three.count}개 / 드로우 ${r.calls}회`]),
    ['C++ wasm', '이번 가이드에서 속도 측정하지 않음', '측정값 없음', '기준 일치·ABI·메모리 진단만 검사']
  ];
  return [
    '<article class="card section cover" id="part6"><h1>6부 · 부록</h1><p>구현 경로·기준 기록·실측 조건·문제 해결·출처를 한곳에서 확인합니다.</p></article>',
    '<article class="card section" id="ch6-reference"><h2>비교와 재현을 위한 참고표</h2><p>측정과 기준 파일에서 표를 생성하며 서로 다른 측정을 성능 순위로 해석하지 않습니다.</p></article>',
    card('tracks', '네 가지 구현 경로', '같은 규칙을 어떤 실행 환경과 표시 방식에 연결했는지 비교합니다. 배포 대상과 도구의 차이를 확인하고 이미 익숙한 경로부터 따라가도 됩니다.', table(['경로', '게임 계산', '화면', '실행 산출물'], [
      ['pygame', 'Python 고정 스텝', 'pygame 이미지', 'Python·pygame 실행 폴더'],
      ['Canvas', 'TypeScript → JS', 'Canvas2D', 'JS가 내장된 HTML'],
      ['Three.js', 'TypeScript → JS', 'WebGL 인스턴스·셰이더', 'Three 번들이 내장된 HTML'],
      ['C++ wasm', 'C++ → wasm, JS 시간/입력', 'Canvas2D·렌더 버퍼', 'wasm·JS·JSON 내장 HTML']
    ])),
    card('levels', '레벨별 추가 책임', '이전 레벨은 독립 폴더로 보존합니다. 새 기능을 추가할 때 그 기능의 경계를 먼저 검사한 뒤 같은 레벨의 기준 기록과 비교합니다.', table(['레벨', '추가 기능'], [
      ['Lv1', '플레이어 이동·발사'], ['Lv2', '적·충돌·목숨'], ['Lv3', '링·조준·나선·파동'], ['Lv4', '보스3단계'],
      ['Lv5', '그레이즈·폭탄·아이템·파워'], ['Lv6', 'JSON 스테이지'], ['Lv7', '시작·정지·종료·입자·소리·저장']
    ])),
    card('goldens', '기준 기록의 마지막 체크포인트', '아래 값은 spec/golden 파일에서 자동으로 읽습니다. 각 레벨의 기존 pygame 기준이며 다른 경로가 실패해도 포트에 맞춰 덮어쓰지 않습니다. 상세 비교는60·600·1800스텝에서 수행합니다.', table(['레벨', '호출', '탄환', '적', '점수', '목숨', '단계', '체크섬'], states)),
    card('time', '호출 횟수와 전투 스텝', 'Lv7은 게임 오버 뒤에도 호출 프레임과 효과 갱신이 이어질 수 있지만 전투 시간은 멈춥니다. 기록의1800호출을1800번의 전투 갱신으로 해석하면 측정 비용을 잘못 비교하게 됩니다.', table(['현재 캡처', '전체 호출', '전투 진행'], [['pygame', py.steps, py.activeSteps], ['Canvas 로직', canvas.steps, canvas.activeSteps]])),
    card('measurements', '실측값과 측정 범위', '이 표는 최신 captures의 실측 보고서를 읽어 생성합니다. Python 프로파일러·Node 로직·정적 WebGL 렌더는 측정 대상과 계측 비용이 다르므로 속도 순위나 게임 FPS로 비교하지 않습니다.', table(['경로', '포함/제외 조건', '기록값', '작업량'], methods)),
    card('environment', '측정 환경과 해석', '사용한 소프트웨어 드라이버와 런타임을 함께 기록합니다. 같은 이름의 GPU API라도 소프트웨어 렌더러의 수치를 실제 GPU 성능으로 일반화할 수 없습니다. 타이머 해상도 때문에 짧은 표본이0ms로 나올 수도 있습니다.', table(['환경 항목', '실제 캡처 값'], [
      ['Python / 기계', `${py.python} / ${py.machine}`], ['Node / 기계', `${canvas.node} / ${canvas.machine}`],
      ['브라우저', three.browser], ['렌더러', three.renderer], ['측정 원본', 'captures/pygame-profile.txt, canvas-profile.txt, three-profile.txt']
    ])),
    card('troubleshooting', '증상별 확인 순서', '먼저 실패하는 경계를 좁히고 해당 단계의 실제 검사 명령을 실행합니다. 실행 결과가 같아도 화면·입력·오디오·저장은 별도의 경로이므로 각 검사를 유지합니다.', table(['증상', '먼저 확인할 것'], [
      ['기준 체크섬 불일치', '입력 변경 시점·갱신 순서·floor·무부호32비트·난수 소비'],
      ['wasm 로딩 실패', '파일 존재·CompileError·내보내기·ABI 버전'],
      ['좌표가 비정상', '주소·바이트 간격·활성 개수·little-endian·뷰 수명'],
      ['WebGL 화면이 검음', '컨텍스트 오류·카메라·실제 픽셀·Mesa 실행 경로'],
      ['소리가 안 남', '사용자 입력 뒤 활성화·포커스·정지 상태·장치 거부'],
      ['최고 점수가 사라짐', '저장소 접근·JSON 형식·안전한 정수 검사']
    ])),
    card('assets', '에셋 출처와 체크섬', '아래 표는 examples/assets/LICENSES.md에서 자동 생성합니다. Noto Emoji PNG와 함께 버전·원본·원문 라이선스·SHA-256을 보관합니다. 에셋을 바꿀 때 표와 실제 파일 검증도 갱신해야 합니다.', licenses),
    card('licenses', '코드·그림·글꼴의 출처 구분', '같은 프로젝트 안에서도 이미지·라이브러리·글꼴은 각각의 원문과 고지를 확인합니다. 합성 소리에는 외부 음원 파일을 사용하지 않았으며 게임의 원 도형은 Canvas와 Three 기하로 만듭니다.', table(['대상', '확인 위치와 조건'], [
      ['Noto 이미지', 'examples/assets/LICENSES.md 및 assets/noto-emoji/LICENSE, APACHE-2.0.txt'],
      ['Three.js', 'examples/three-ts/LICENSE-THREE.txt, 설치 패키지의 MIT 원문과 비교'],
      ['덱 고정폭 글꼴', '템플릿의 DeckMono/D2Coding 고지와 embed_mono_font.py 검사'],
      ['의존성 코드', '고정 package.json·잠금 파일과 설치 패키지의 라이선스']
    ])),
    card('glossary', '핵심 용어 찾아보기', '같은 용어를 게임 규칙과 표시 구현에서 혼용하지 않습니다. 특히 활성 개수·할당 용량·표시 횟수·게임 스텝은 서로 다른 값입니다.', table(['용어', '뜻'], [
      ['고정 스텝', '게임을 일정한 논리 시간 단위로 한 번 갱신'], ['보간', '이전·현재 상태로 표시 위치 계산'],
      ['풀', '미리 확보한 공간과 연속 활성 구간'], ['교환 삭제', '마지막 활성 요소를 지운 위치로 이동'],
      ['ABI', '호출 이름·자료형·메모리 배치의 약속'], ['선형 메모리', 'wasm에서 바이트 주소로 접근하는 공간'],
      ['결정성', '같은 초기 상태와 입력에서 같은 결과'], ['체크섬', '양자화한 게임 상태를 비교하는 요약 값']
    ])),
    card('distribution', '실행과 재빌드 구분', '완성 HTML을 여는 독자와 예제를 다시 컴파일하는 작성자에게 필요한 도구는 다릅니다. 오프라인 HTML에는 실행 자원이 내장되지만 빌드에는 고정된 도구와 소스가 필요합니다.', table(['작업', '확인 사항'], [
      ['가이드 읽기', '탄막-슈팅-가이드.html 단독 열기·목차·데모'], ['브라우저 예제 실행', 'dist의 해당 레벨 HTML·화면 클릭·키보드 입력'],
      ['C++ 재빌드', 'g++·clang++·wasm-ld·Node·esbuild'], ['pygame 실행', 'Python·pygame·함께 배포한 이미지/라이선스'],
      ['전체 검사', 'npm test, 제한된 메모리에서는 순차 테스트와 Mesa 경로']
    ])),
    card('extension', '다음 기능을 추가하는 순서', '규칙 변경과 렌더 변경을 작은 단위로 나눕니다. 입력과 상태의 약속을 먼저 정하고 실패 경계를 검사한 뒤 네이티브·브라우저·오프라인 산출물을 확인합니다. 기준 변경이 필요한 기능은 기존 레벨과 기준을 보존한 새 단계로 추가합니다.', '<div class="flow"><div class="box">규칙과 입력</div><div class="arr">→</div><div class="box">상태와 경계 검사</div><div class="arr">→</div><div class="box">기준 비교</div><div class="arr">→</div><div class="box">화면·배포 검사</div></div>'),
    '<article class="card quiz" id="p6-reference-quiz" data-quiz><h3>비교와 재현 · 이해 확인</h3><p class="q">Node 로직 측정과 정적 WebGL 렌더 측정의 숫자로 어느 게임이 더 빠른지 정할 수 있을까요?</p><button>답 보기</button><div class="a">측정 작업·포함 비용·환경이 달라 직접 순위를 정할 수 없습니다. 같은 조건과 작업량을 정하고 필요한 항목을 실제로 측정해야 합니다.</div></article>'
  ].join('\n\n') + '\n';
}

export function writeAppendix() {
  writeFileSync(new URL('parts/60-appendix.html', src), renderAppendix());
}
if (process.argv[1] === fileURLToPath(import.meta.url)) writeAppendix();
