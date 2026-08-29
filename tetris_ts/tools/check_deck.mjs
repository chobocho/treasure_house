// tools/check_deck.mjs — 완성된 덱을 진짜 브라우저로 열어 본다.
//
// 검사하는 것 (저장소 CLAUDE.md §3 의 요건):
//   · Galaxy Fold 접힘(374px)·펼침(768px) 두 폭에서 가로로 넘치지 않는가
//   · ←/→ 로 페이지가 넘어가고 카운터가 따라오는가
//   · 목차에서 특정 장으로 뛸 수 있는가
//   · 콘솔에 오류가 찍히지 않는가 (데모가 조용히 죽는 걸 잡는다)
//
// 이 기계에는 playwright 가 npx 캐시에만 있다. node_modules 에 심볼릭 링크를 걸면
// 이 프로젝트의 typescript 설치와 부딪히므로, 절대 경로로 직접 임포트한다.
//
//   node tools/check_deck.mjs [덱경로]

import { fileURLToPath } from 'node:url';
import { dirname, join, resolve } from 'node:path';
import { existsSync } from 'node:fs';

const PW = '/root/.npm/_npx/e41f203b7505f1fb/node_modules/playwright/index.mjs';
const HERE = dirname(fileURLToPath(import.meta.url));
const DECK = resolve(process.argv[2] ?? join(HERE, '..', '..', 'TypeScript_테트리스_AI_8인_대전.html'));

if (!existsSync(DECK)) {
  console.error(`덱이 없다: ${DECK}\n  먼저 make deck 을 돌려라.`);
  process.exit(1);
}
if (!existsSync(PW)) {
  console.error(`playwright 를 못 찾았다: ${PW}`);
  process.exit(1);
}

const { chromium } = await import(PW);
const WIDTHS = [
  { w: 374, h: 800, name: '접힘 374px' },
  { w: 768, h: 900, name: '펼침 768px' },
];

let fail = 0;
const browser = await chromium.launch();   // 한 번에 브라우저 하나만 띄운다 (메모리 제약)
try {
  for (const { w, h, name } of WIDTHS) {
    const page = await browser.newPage({ viewport: { width: w, height: h } });
    const errs = [];
    page.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
    page.on('pageerror', (e) => errs.push(String(e)));
    await page.goto('file://' + DECK);
    await page.waitForSelector('.slide');

    const total = await page.evaluate(() => document.querySelectorAll('.slide').length);
    const read = () => page.evaluate(() => ({
      counter: document.getElementById('counter').textContent.trim(),
      // 가로 넘침은 문서 전체와 보이는 슬라이드 양쪽에서 본다.
      docOver: document.documentElement.scrollWidth - document.documentElement.clientWidth,
      wide: [...document.querySelectorAll('.slide')]
        .filter((s) => s.style.display !== 'none')
        .flatMap((s) => [...s.querySelectorAll('*')])
        // SVG 안쪽은 제외한다 — viewBox 로 스케일되므로 scrollWidth/clientWidth 비교가
        // 의미가 없다(차트의 <text> 가 늘 '넘친 것'으로 잡힌다).
        .filter((el) => !(el instanceof SVGElement) &&
          el.scrollWidth > el.clientWidth + 2 &&
          getComputedStyle(el).overflowX === 'visible')
        .map((el) => el.tagName + '.' + (el.className || '') + ' ' + el.scrollWidth + '>' + el.clientWidth)
        .slice(0, 5),
    }));

    let worst = 0, overflows = [], demoBad = [];
    for (let i = 1; i <= total; i++) {
      const st = await read();
      worst = Math.max(worst, st.docOver);
      if (st.docOver > 1 || st.wide.length) overflows.push(`${i}쪽: 문서 +${st.docOver}px ${st.wide.join(' | ')}`);
      // 데모가 붙는 슬라이드면 실제로 캔버스가 생겼는지 본다. 조용히 죽는 데모를 잡는 유일한 방법이다.
      const demo = await page.evaluate(() => {
        const s = [...document.querySelectorAll('.slide')].find((x) => x.style.display !== 'none');
        const h = s && s.querySelector('[data-demo]');
        if (!h) return null;
        return { name: h.dataset.demo, canvas: h.querySelectorAll('canvas').length, warn: !!h.querySelector('.warn') };
      });
      if (demo && (demo.canvas === 0 || demo.warn)) {
        demoBad.push(`${i}쪽: 데모 ${demo.name} — 캔버스 ${demo.canvas}개${demo.warn ? ', 오류 상자 떴음' : ''}`);
      }
      if (i < total) await page.keyboard.press('ArrowRight');
    }
    const last = await read();
    const okLast = last.counter === `${total} / ${total}`;

    // 목차로 1장으로 되돌아오기
    await page.click('#tocBtn');
    await page.click('#toc a[data-go="1"]');
    const back = await read();

    const bad = overflows.length || demoBad.length || !okLast
      || back.counter !== `1 / ${total}` || errs.length;
    console.log(`${bad ? '✖' : '✔'} ${name} — ${total}장 훑음, 최대 가로 넘침 ${worst}px, ` +
      `끝 카운터 ${last.counter}, 목차 복귀 ${back.counter}, 콘솔 오류 ${errs.length}건, ` +
      `데모 이상 ${demoBad.length}건`);
    for (const o of overflows.slice(0, 8)) console.log('    ' + o);
    for (const d of demoBad.slice(0, 8)) console.log('    ' + d);
    for (const e of errs.slice(0, 5)) console.log('    콘솔: ' + e);
    if (bad) fail++;
    await page.close();
  }
} finally {
  await browser.close();
}
process.exit(fail ? 1 : 0);
