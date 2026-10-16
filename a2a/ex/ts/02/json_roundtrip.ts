// 교통 견적 요청을 JSON 으로 쓰고 다시 읽는다 — JSON 전역 객체.
// region: roundtrip
const req = { headcount: 30, nights: 1, depart: "강남역" };

// 빈칸 없이, 한글은 그대로 쓴다
const text = JSON.stringify(req);
console.log("쓰기    :", text);

// 되읽은 값의 타입은 알 수 없다(any) — 모양을 믿는다고 적어 준다
type BusRequest = { headcount: number; nights: number; depart: string };
const back = JSON.parse(text) as BusRequest;
console.log("되읽기  :", typeof back, back.depart);
console.log("인원    :", back.headcount, typeof back.headcount);
// endregion
