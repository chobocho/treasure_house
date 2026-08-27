// ============================================================================
//  ga_browser.js — 브라우저에서 GA를 직접 돌린다 (이 문서 안에서, 지금)
//
//  Node 트레이너와 알고리즘은 완전히 같다 — 난수·선택·교차·변이는 ga_core.mjs
//  의 함수를 그대로 쓴다. 다른 건 딱 두 가지다.
//    1) 규모: 개체 12, 세대 40, 조각 120 (노트북 40초짜리를 8초로 줄인 설정)
//    2) 시간 쪼개기: 한 프레임에 20 ms 만 계산하고 화면에 양보한다
//  워커를 쓰지 않은 이유는 마지막 슬라이드에서 따로 다룬다.
// ============================================================================
class GaRunner {
  constructor(host, opts = {}) {
    this.host = host;
    this.POP = opts.pop ?? 12;
    this.GEN = opts.gen ?? 40;
    this.SEEDS = opts.seeds ?? [1, 2];
    this.PIECES = opts.pieces ?? 120;
    this.BUDGET = opts.budget ?? 20;         // 프레임당 계산 예산 (ms)
    this.ELITE = 2; this.K = 3;
    host.classList.add('garow');
    host.innerHTML = `
      <div class="gapanel">
        <div class="gactl">
          <button class="ga-run">▶ 학습 시작</button>
          <button class="ga-reset">처음부터</button>
          <span class="ga-gen">세대 0 / ${this.GEN}</span>
        </div>
        <canvas class="gachart"></canvas>
        <div class="gawts"></div>
        <div class="gahint small mut">최고 개체의 가중치가 오른쪽 AI에 즉시 반영된다.</div>
      </div>
      <div class="gaboard"></div>`;
    this.chart = host.querySelector('.gachart');
    this.genEl = host.querySelector('.ga-gen');
    this.wts = host.querySelector('.gawts');
    this.btn = host.querySelector('.ga-run');
    this.btn.onclick = () => { this.playing = !this.playing; this.syncBtn(); };
    host.querySelector('.ga-reset').onclick = () => this.reset();
    this.log = [];
    this.playing = false;
    this.ready = false;
    this.boot(host.querySelector('.gaboard'));
  }

  async boot(boardHost) {
    this.core = await loadCore(WASM_B64, 1);                    // 적합도 평가 전용
    this.demoCore = await loadCore(WASM_B64, (Math.random() * 0xffffffff) >>> 0);
    this.driver = new AiDriver(this.demoCore, { thinkMs: 90, moveMs: 24, weights: GA_WEIGHTS.levels.easy });
    this.view = new TetrisView(boardHost, this.demoCore, { driver: this.driver, manual: true, compact: true, autoRestart: true });
    this.view.sent = 0;
    this.ready = true;
    this.reset();
  }

  reset() {
    this.rnd = mulberry32(20260827);
    this.pop = Array.from({ length: this.POP }, () => randomGenome(this.rnd));
    this.fits = new Array(this.POP).fill(null);
    this.evals = new Array(this.POP).fill(null);
    this.i = 0; this.gen = 0;
    this.log = [];
    this.best = null; this.bestFit = -1;
    this.playing = false;
    this.syncBtn();
    this.paint();
  }
  syncBtn() { this.btn.textContent = this.playing ? '❚❚ 멈춤' : '▶ 학습 시작'; }

  // 적합도 = 이 가중치로 두 판을 두고 보낸 줄 수의 평균. Node 쪽과 같은 정의다.
  fitness(g) {
    setWeights(this.core, g);
    let attack = 0, lines = 0;
    for (const s of this.SEEDS) {
      lines += this.core.e.ai_play(s >>> 0, this.PIECES);
      attack += this.core.e.ai_play_attack();
    }
    return { attack: attack / this.SEEDS.length, lines: lines / this.SEEDS.length };
  }

  // 한 프레임에 허용된 시간만큼만 개체를 평가한다.
  // 브라우저에서 오래 도는 계산의 핵심은 "얼마나 빠른가"가 아니라 "언제 양보하는가"다.
  work() {
    if (!this.ready || !this.playing || this.gen >= this.GEN) return;
    const t0 = performance.now();
    while (this.i < this.POP && performance.now() - t0 < this.BUDGET) {
      const ev = this.fitness(this.pop[this.i]);
      this.evals[this.i] = ev;
      this.fits[this.i] = ev.attack;
      this.i++;
    }
    if (this.i < this.POP) return;
    this.nextGeneration();
  }

  nextGeneration() {
    const order = this.fits.map((f, i) => [f, i]).sort((a, b) => b[0] - a[0]);
    const bi = order[0][1];
    if (this.fits[bi] > this.bestFit) { this.bestFit = this.fits[bi]; this.best = this.pop[bi].slice(); }
    this.gen++;
    this.log.push({
      gen: this.gen,
      best: +this.fits[bi].toFixed(1),
      mean: +(this.fits.reduce((s, x) => s + x, 0) / this.POP).toFixed(1),
    });
    if (this.driver && this.best) this.driver.setWeights(this.best);   // 눈앞의 AI가 바로 세진다

    const next = order.slice(0, this.ELITE).map(([, i]) => this.pop[i].slice());
    while (next.length < this.POP) {
      const a = tournament(this.pop, this.fits, this.K, this.rnd);
      const b = tournament(this.pop, this.fits, this.K, this.rnd);
      next.push(mutate(crossover(a, b, this.rnd), this.rnd));
    }
    this.pop = next;
    this.fits.fill(null);
    this.i = 0;
    if (this.gen >= this.GEN) { this.playing = false; this.syncBtn(); }
    this.paint();
  }

  paint() {
    this.genEl.textContent = `세대 ${this.gen} / ${this.GEN}` +
      (this.bestFit >= 0 ? ` · 최고 ${this.bestFit.toFixed(1)}줄 보냄` : '');
    if (this.log.length >= 2) drawGaChart(this.chart, this.log, this.log.length);
    const w = this.best || this.pop[0];
    this.wts.innerHTML = w.map((v, i) => {
      const pct = Math.min(50, Math.abs(v) * 50);
      const side = v >= 0
        ? `<i style="left:50%;width:${pct}%;background:#4ade80"></i>`
        : `<i style="right:50%;width:${pct}%;background:#f87171"></i>`;
      return `<div class="wrow"><span>${FEAT_KO[i]}</span><div class="wbar">${side}</div><b>${v.toFixed(2)}</b></div>`;
    }).join('');
  }

  start() {
    if (this.running) return;
    this.running = true;
    this.last = performance.now();
    this.acc = 0;
    const loop = (now) => {
      if (!this.running) return;
      let dt = now - this.last; this.last = now;
      if (dt > 250) dt = 250;
      this.acc += dt;
      while (this.acc >= 16) { if (this.view) this.view.step16(); this.acc -= 16; }
      if (this.view) this.view.frame();
      this.work();
      this.raf = requestAnimationFrame(loop);
    };
    this.raf = requestAnimationFrame(loop);
  }
  stop() { this.running = false; if (this.raf) cancelAnimationFrame(this.raf); }
}

DEMO_MOUNTS['ga'] = async (host) => new GaRunner(host, {});
