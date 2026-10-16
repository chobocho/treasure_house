// 워크숍 규칙 — 입력과 자료만으로 답이 정해지는 순수 함수들.
// A2A 와는 무관한 '업무 로직'이다. 에이전트는 이 함수를 부르고 결과를
// A2A 메시지·아티팩트로 감싸기만 한다. 결과 모양은 골든 파일이 정한다.
import { workshop, type MealType, type Menu } from "./fixtures.ts";

const BAD_SIZE = "인원과 박 수는 1 이상이어야 합니다";
const BAD_VEG = "채식 인원은 0명 이상, 전체 인원 이하여야 합니다";

export type Fail = { ok: false; reason: string };

export type LodgingRequest = {
  date: string;
  nights: number;
  headcount: number;
};
export type LodgingQuote = {
  ok: true;
  venueId: string;
  venueName: string;
  rooms: number;
  nights: number;
  headcount: number;
  total: number;
};

const badSize = (headcount: number, nights: number) =>
  headcount < 1 || nights < 1;

function addDays(iso: string, n: number): string {
  // 자정 UTC 로 고정해야 시간대와 서머타임에 흔들리지 않는다.
  const t = Date.parse(`${iso}T00:00:00Z`) + n * 86_400_000;
  return new Date(t).toISOString().slice(0, 10);
}

// 숙박 가능한 곳 중 총액이 가장 싼 곳. O(숙소 수 × 박 수).
export function chooseLodging(
  req: LodgingRequest,
): LodgingQuote | Fail {
  const { headcount: hc, nights } = req;
  if (badSize(hc, nights)) return { ok: false, reason: BAD_SIZE };
  const stay = Array.from({ length: nights }, (_, i) =>
    addDays(req.date, i),
  );
  let best: { total: number; id: string; quote: LodgingQuote } | null =
    null;
  for (const v of workshop.venues) {
    if (v.capacity < hc || stay.some((d) => v.closed.includes(d))) {
      continue;
    }
    const total = hc * v.pricePerPersonNight * nights;
    // 같은 값이면 id 가 작은 쪽 — 언어마다 정렬이 달라도 답이 같게.
    if (
      best === null ||
      total < best.total ||
      (total === best.total && v.id < best.id)
    ) {
      const quote: LodgingQuote = {
        ok: true,
        venueId: v.id,
        venueName: v.name,
        rooms: Math.ceil(hc / v.roomSize),
        nights,
        headcount: hc,
        total,
      };
      best = { total, id: v.id, quote };
    }
  }
  return best?.quote ?? { ok: false, reason: "가능한 숙소가 없습니다" };
}

// n박이면 저녁·아침을 n번, 마지막 날 점심 한 번 — 2n+1 끼.
export function mealSlots(nights: number): string[] {
  const slots: string[] = [];
  for (let i = 1; i <= nights; i++) {
    slots.push(`day${i}-dinner`, `day${i + 1}-breakfast`);
  }
  slots.push(`day${nights + 1}-lunch`);
  return slots;
}

export type MealsRequest = {
  nights: number;
  headcount: number;
  vegetarians: number;
  caps?: Partial<Record<MealType, number>>;
};
export type Choice = {
  id: string;
  name: string;
  price: number;
  count: number;
};
export type Slot = {
  slot: string;
  regular: Choice | null;
  vegetarian: Choice | null;
};
export type MealPlan = { ok: true; slots: Slot[]; total: number };

// 상한 이하에서 가장 비싼 메뉴. 같은 값이면 id 가 작은 쪽.
function pick(kind: MealType, veg: boolean, cap: number): Menu | null {
  const fits = workshop.menus.filter(
    (m) => m.type === kind && m.vegetarian === veg && m.price <= cap,
  );
  fits.sort((a, b) => b.price - a.price || (a.id < b.id ? -1 : 1));
  return fits[0] ?? null;
}

// 끼니마다 일반식·채식을 고른다. O(끼니 수 × 메뉴 수).
export function planMeals(req: MealsRequest): MealPlan | Fail {
  const { headcount: hc, nights, vegetarians: veg } = req;
  if (badSize(hc, nights)) return { ok: false, reason: BAD_SIZE };
  if (veg < 0 || veg > hc) return { ok: false, reason: BAD_VEG };
  const caps = { ...workshop.defaultCaps, ...req.caps };
  const slots: Slot[] = [];
  let total = 0;
  for (const slot of mealSlots(nights)) {
    const kind = slot.split("-")[1] as MealType;
    const sides: [keyof Omit<Slot, "slot">, number, boolean][] = [
      ["regular", hc - veg, false],
      ["vegetarian", veg, true],
    ];
    const row: Slot = { slot, regular: null, vegetarian: null };
    for (const [side, count, isVeg] of sides) {
      if (count === 0) continue; // 먹을 사람이 없으면 고르지 않는다
      const m = pick(kind, isVeg, caps[kind]);
      if (m === null) {
        return { ok: false, reason: "예산 안에 맞는 메뉴가 없습니다" };
      }
      row[side] = { id: m.id, name: m.name, price: m.price, count };
      total += m.price * count;
    }
    slots.push(row);
  }
  return { ok: true, slots, total };
}

export type BusRequest = { headcount: number; nights: number };
export type BusPlan = {
  ok: true;
  vehicles: { id: string; count: number }[];
  days: number;
  costPerDay: number;
  total: number;
};

// 45인승 a대 + 25인승 b대로 좌석을 채우는 가장 싼 조합.
// a 를 모두 시도한다 — O(h/45), 워크숍 규모에선 충분.
// 같은 값이면 차가 적은 쪽, 그다음 45인승이 많은 쪽.
export function chooseBuses(req: BusRequest): BusPlan | Fail {
  const { headcount: hc, nights } = req;
  if (badSize(hc, nights)) return { ok: false, reason: BAD_SIZE };
  const big = workshop.buses.find((b) => b.id === "bus45")!;
  const small = workshop.buses.find((b) => b.id === "bus25")!;
  let best: [number, number, number] | null = null; // [cost, a, b]
  for (let a = 0; a <= Math.ceil(hc / big.seats); a++) {
    const left = Math.max(0, hc - a * big.seats);
    const b = Math.ceil(left / small.seats);
    const cost = a * big.pricePerDay + b * small.pricePerDay;
    if (
      best === null ||
      cost < best[0] ||
      (cost === best[0] && a + b < best[1] + best[2]) ||
      (cost === best[0] && a + b === best[1] + best[2] && a > best[1])
    ) {
      best = [cost, a, b];
    }
  }
  const [cost, a, b] = best!;
  const vehicles = (
    [
      ["bus45", a],
      ["bus25", b],
    ] as const
  )
    .filter(([, n]) => n > 0)
    .map(([id, count]) => ({ id, count }));
  const days = nights + 1;
  return {
    ok: true,
    vehicles,
    days,
    costPerDay: cost,
    total: cost * days,
  };
}

export type SettleRequest = {
  items: { name: string; amount: number }[];
  budget: number;
  approved: boolean;
};
export type SettleResult =
  | { ok: true; status: "auth-required"; total: number }
  | {
      ok: true;
      status: "completed";
      total: number;
      budget: number;
      remaining: number;
    }
  | { ok: false; reason: string; over: number };

// 예산 초과를 먼저 보고, 그다음 결재 필요 여부를 본다.
export function settle(req: SettleRequest): SettleResult {
  const total = req.items.reduce((s, it) => s + it.amount, 0);
  const { budget } = req;
  if (total > budget) {
    return {
      ok: false,
      reason: "예산을 초과합니다",
      over: total - budget,
    };
  }
  if (total > workshop.approvalThreshold && !req.approved) {
    return { ok: true, status: "auth-required", total };
  }
  return {
    ok: true,
    status: "completed",
    total,
    budget,
    remaining: budget - total,
  };
}

// Go 의 RE2 에는 뒤보기(lookbehind)가 없다. 세 언어가 같은 정규식을
// 쓰려고, 채식 인원을 먼저 찾아 지운 다음 전체 인원을 찾는다.
const VEG = /채식\s*(\d+)명/;
const DATE = /(\d{4}-\d{2}-\d{2})/;
const NIGHTS = /(\d+)박/;
const HEADCOUNT = /(\d+)명/;
const BUDGET = /예산\s*([\d,]+)원/;
const DEPART = /출발\s*(\S+)/;

export type ParsedRequest =
  | {
      ok: true;
      date: string;
      nights: number;
      headcount: number;
      vegetarians: number;
      budget: number | null;
      depart: string | null;
    }
  | { ok: false; missing: string[] };

// 자유 문장에서 날짜·박 수·인원·채식·예산·출발지를 뽑는다.
export function parseRequest(text: string): ParsedRequest {
  const veg = VEG.exec(text);
  const rest = text.replace(VEG, ""); // g 플래그가 없으니 첫 번째만
  const date = DATE.exec(rest);
  const nights = NIGHTS.exec(rest);
  const headcount = HEADCOUNT.exec(rest);
  const found = { date, nights, headcount };
  const missing = Object.entries(found)
    .filter(([, m]) => m === null)
    .map(([k]) => k);
  if (date === null || nights === null || headcount === null) {
    return { ok: false, missing };
  }
  const budget = BUDGET.exec(rest);
  const depart = DEPART.exec(rest);
  return {
    ok: true,
    date: date[1]!,
    nights: Number(nights[1]),
    headcount: Number(headcount[1]),
    vegetarians: veg ? Number(veg[1]) : 0,
    budget: budget ? Number(budget[1]!.replaceAll(",", "")) : null,
    depart: depart ? depart[1]! : null,
  };
}
