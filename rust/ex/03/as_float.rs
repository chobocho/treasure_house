fn main() {
    // 정수 → 실수: 3장에서 미뤄 둔 평균
    let total = 247;
    let count = 3;
    println!("평균 = {}", total as f64 / count as f64);
    // 실수 → 정수: 소수점 아래를 0 쪽으로 버린다
    println!("2.9 as i32   = {}", 2.9 as i32);
    println!("-2.9 as i32  = {}", -2.9 as i32);
    // 범위를 넘으면 그 타입의 끝값에서 멈춘다
    println!("300.7 as u8  = {}", 300.7 as u8);
    println!("-5.0 as u8   = {}", -5.0 as u8);
    println!("1e20 as i32  = {}", 1e20 as i32);
    println!("inf as i32   = {}", f64::INFINITY as i32);
    // NaN 은 0 이 된다
    println!("NaN as i32   = {}", f64::NAN as i32);
    // 반올림하려면 round 를 먼저 부른다
    println!("2.9 를 반올림 = {}", 2.9_f64.round() as i32);
}
