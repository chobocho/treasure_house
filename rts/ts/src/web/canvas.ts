// 320×200 인덱스 프레임버퍼를 캔버스에 올린다 — 그리기는 하지 않는다.
//
// 엔진의 render.draw() 는 팔레트 번호 하나가 든 320×200 배열을 채운다. 브라우저는
// 그 배열을 화면에 못 올리므로 여기서 RGBA 로 편다. 그 이상은 하지 않는다.
// 선 하나라도 여기서 그리기 시작하면 "화면에 보이는 것 = 엔진이 그린 것" 이라는
// 이 덱의 유일한 주장이 무너진다.
//
// 팔레트 값은 0…63 (VGA DAC) 이므로 raster.expand() 로 0…255 로 편다. 세 언어의
// PPM 출력이 쓰는 것과 같은 함수다 — 브라우저 화면과 out/frame_*.ppm 이 같은 색이다.
import * as C from '../const';
import * as RS from '../raster';

export const W = C.SCR_W;
export const H = C.SCR_H;

// 팔레트 → RGBA 룩업 1024바이트. 색 하나당 네 칸(R,G,B,A)이다.
export function paletteLut(pal: RS.RGB[]): Uint8ClampedArray {
  const lut = new Uint8ClampedArray(256 * 4);
  for (let i = 0; i < 256; i += 1) {
    const c = i < pal.length ? pal[i] : ([0, 0, 0] as RS.RGB);
    lut[i * 4] = RS.expand(c[0]);
    lut[i * 4 + 1] = RS.expand(c[1]);
    lut[i * 4 + 2] = RS.expand(c[2]);
    lut[i * 4 + 3] = 255;
  }
  return lut;
}

// 320×200 을 정수배로 키워 보여 준다. 확대는 캔버스가 하고(보간 끔),
// 우리는 등배 ImageData 하나만 유지한다 — 프레임마다 새로 만들지 않는다.
export class Screen {
  readonly canvas: HTMLCanvasElement;
  readonly w: number;
  readonly h: number;
  private readonly ctx: CanvasRenderingContext2D;
  private readonly back: HTMLCanvasElement;
  private readonly bctx: CanvasRenderingContext2D;
  private readonly img: ImageData;
  private lut: Uint8ClampedArray;

  constructor(scale = 2, w = W, h = H) {
    this.w = w;
    this.h = h;
    this.canvas = document.createElement('canvas');
    this.canvas.width = w * scale;
    this.canvas.height = h * scale;
    this.canvas.style.width = '100%';
    this.canvas.style.maxWidth = w * scale + 'px';
    this.canvas.style.display = 'block';
    this.canvas.style.imageRendering = 'pixelated';
    this.canvas.style.background = '#000';
    this.canvas.style.borderRadius = '6px';
    this.canvas.style.touchAction = 'none';
    this.ctx = this.canvas.getContext('2d') as CanvasRenderingContext2D;
    this.back = document.createElement('canvas');
    this.back.width = w;
    this.back.height = h;
    this.bctx = this.back.getContext('2d') as CanvasRenderingContext2D;
    this.img = this.bctx.createImageData(w, h);
    this.lut = paletteLut(RS.buildPalette());
  }

  // 물 색 순환(§22.3)처럼 팔레트만 바뀌는 경우를 위해 따로 둔다.
  setPalette(pal: RS.RGB[]): void {
    this.lut = paletteLut(pal);
  }

  // 인덱스 배열 → 화면. 할당이 없다 — 애니메이션 루프 안에서 매 프레임 불린다.
  paint(fb: ArrayLike<number>): void {
    const d = this.img.data;
    const lut = this.lut;
    const n = this.w * this.h;
    for (let i = 0; i < n; i += 1) {
      const s = fb[i] * 4;
      const t = i * 4;
      d[t] = lut[s];
      d[t + 1] = lut[s + 1];
      d[t + 2] = lut[s + 2];
      d[t + 3] = 255;
    }
    this.bctx.putImageData(this.img, 0, 0);
    this.ctx.imageSmoothingEnabled = false;
    this.ctx.drawImage(this.back, 0, 0, this.canvas.width, this.canvas.height);
  }

  // 마우스 이벤트 → 320×200 좌표. CSS 로 늘어난 만큼 되돌린다.
  // 화면 밖이면 붙잡지 않고 그대로 돌려준다 — 판정은 부르는 쪽(select.inView)이 한다.
  eventPos(e: { clientX: number; clientY: number }): [number, number] {
    const r = this.canvas.getBoundingClientRect();
    const sx = r.width > 0 ? this.w / r.width : 1;
    const sy = r.height > 0 ? this.h / r.height : 1;
    return [Math.floor((e.clientX - r.left) * sx),
            Math.floor((e.clientY - r.top) * sy)];
  }
}
