fn main() {
    let x = 5; // 문: 값을 내지 않는다
    let y = x + 1; // x + 1 은 식: 값을 낸다
    let z = if y > 5 { "크다" } else { "작다" }; // if 도 식
    let unit = println!("{y} {z}"); // 매크로 호출도 식 — 값은 ()
    println!("{unit:?}");
}
