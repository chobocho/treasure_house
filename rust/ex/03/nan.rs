fn main() {
    let zero = 0.0_f64;
    let inf = 1.0 / zero;
    let nan = zero / zero;
    println!("1.0 / 0.0  = {inf}");
    println!("-1.0 / 0.0 = {}", -1.0 / zero);
    println!("0.0 / 0.0  = {nan}");
    println!("inf + 1.0  = {}", inf + 1.0);
    println!("inf - inf  = {}", inf - inf);
    // NaN 은 무엇과 견주어도 거짓이다 — 자기 자신과도
    println!("nan == nan ? {}", nan == nan);
    println!("nan < 1.0  ? {}", nan < 1.0);
    println!("nan > 1.0  ? {}", nan > 1.0);
    // 그래서 NaN 인지는 메서드로 묻는다
    println!("nan.is_nan()    ? {}", nan.is_nan());
    println!("inf.is_finite() ? {}", inf.is_finite());
    println!("nan.is_finite() ? {}", nan.is_finite());
}
