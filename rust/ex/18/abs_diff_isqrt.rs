fn main() {
    // 두 재고의 차이 — 어느 쪽이 큰지 모른다
    let (a, b): (u32, u32) = (3, 10);
    // a - b 는 u32 에 없는 값이다
    println!("checked_sub {:?}", a.checked_sub(b));
    println!("abs_diff    {} {}", a.abs_diff(b), b.abs_diff(a));
    // 부호 있는 타입의 abs_diff 는 부호 없는 타입으로 답한다
    let d: u32 = i32::MIN.abs_diff(i32::MAX);
    println!("MIN 과 MAX  {d}");

    // 정수 제곱근 — 소수점 아래를 버린 값
    let n = u64::MAX;
    println!("n           {n}");
    println!("isqrt       {}", n.isqrt());
    // f64 는 n 을 그대로 담지 못한다 — 거치면 답이 하나 크다
    println!("n as f64    {}", n as f64);
    let via_float = (n as f64).sqrt() as u64;
    println!("f64 를 거쳐 {via_float}");
    println!("제곱        {:?}", via_float.checked_mul(via_float));
}
