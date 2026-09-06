// 캔버스 프런트엔드 — 8비트 인덱스 버퍼를 팔레트로 풀어 화면에 올린다.
//
// 엔진은 320x200 짜리 팔레트 인덱스 배열만 만든다. 여기서 하는 일은
// 모드 13h 시절 VGA DAC 가 하던 일과 정확히 같다 — 인덱스를 RGB 로 바꾸는 것.
// 그래서 이 파일에는 게임 로직이 한 줄도 없다.

import { PAL_SIZE, SCR_H, SCR_W, cyclePalette, expand6 } from '../raster';
import type { Rgb } from '../raster';

/** 팔레트를 RGBA 룩업으로 미리 펴 둔다. 픽셀마다 세 번 조회하는 것보다 싸다. */
function paletteLut(pal: Rgb[]): Uint8ClampedArray {
  const lut = new Uint8ClampedArray(PAL_SIZE * 4);
  for (let i = 0; i < PAL_SIZE; i++) {
    const c = pal[i] as Rgb;
    lut[i * 4] = expand6(c[0]);
    lut[i * 4 + 1] = expand6(c[1]);
    lut[i * 4 + 2] = expand6(c[2]);
    lut[i * 4 + 3] = 255;
  }
  return lut;
}

export class CanvasView {
  readonly canvas: HTMLCanvasElement;
  private ctx: CanvasRenderingContext2D;
  private img: ImageData;
  private buf: Uint8ClampedArray;
  private lut: Uint8ClampedArray;
  private basePal: Rgb[];
  private phase = -1;

  constructor(pal: Rgb[], scale: number) {
    this.basePal = pal;
    this.lut = paletteLut(pal);
    const cv = document.createElement('canvas');
    cv.width = SCR_W;
    cv.height = SCR_H;
    // 확대는 CSS 로 한다. 캔버스를 크게 잡고 그리면 픽셀마다 비용이 배로 든다.
    cv.style.width = String(SCR_W * scale) + 'px';
    cv.style.height = String(SCR_H * scale) + 'px';
    cv.style.imageRendering = 'pixelated';
    cv.style.display = 'block';
    cv.style.maxWidth = '100%';
    this.canvas = cv;
    const c = cv.getContext('2d');
    if (!c) throw new Error('2d 컨텍스트를 못 얻었다');
    this.ctx = c;
    this.img = this.ctx.createImageData(SCR_W, SCR_H);
    this.buf = this.img.data;
  }

  /** 화면 폭에 맞춰 CSS 크기를 다시 잡는다. 정수 배율만 쓴다 — 그래야 픽셀이 안 뭉갠다. */
  fit(availWidth: number): void {
    let s = Math.floor(availWidth / SCR_W);
    if (s < 1) s = 1;
    if (s > 4) s = 4;
    this.canvas.style.width = String(SCR_W * s) + 'px';
    this.canvas.style.height = String(SCR_H * s) + 'px';
  }

  /** 팔레트 사이클링 위상이 바뀌었을 때만 룩업을 다시 만든다. */
  setPhase(phase: number): void {
    if (phase === this.phase) return;
    this.phase = phase;
    this.lut = paletteLut(cyclePalette(this.basePal, phase));
  }

  draw(fb: Uint8Array): void {
    const buf = this.buf;
    const lut = this.lut;
    const n = SCR_W * SCR_H;
    for (let i = 0; i < n; i++) {
      const c = (fb[i] as number) * 4;
      const j = i * 4;
      buf[j] = lut[c] as number;
      buf[j + 1] = lut[c + 1] as number;
      buf[j + 2] = lut[c + 2] as number;
      buf[j + 3] = 255;
    }
    this.ctx.putImageData(this.img, 0, 0);
  }
}
