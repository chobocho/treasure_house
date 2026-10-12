fn main() {
    // f64 는 64 비트 — to_bits 가 그 비트를 u64 로 준다
    let one: f64 = 1.0;
    println!("1.0   {:#018x}", one.to_bits());
    println!("-1.0  {:#018x}", (-one).to_bits());
    // 맨 왼쪽 비트가 부호다
    let sign = |x: f64| x.to_bits() >> 63;
    println!("부호 비트 {} {}", sign(one), sign(-one));

    // 0.1 + 0.2 와 0.3 은 마지막 비트 하나가 다르다
    let sum: f64 = 0.1 + 0.2;
    let lit: f64 = 0.3;
    println!("sum   {:#018x}", sum.to_bits());
    println!("0.3   {:#018x}", lit.to_bits());
    println!("차이  {}", sum.to_bits() - lit.to_bits());
    // from_bits 는 비트에서 f64 를 만든다
    let next = f64::from_bits(lit.to_bits() + 1);
    println!("{next} {}", next == sum);
}
