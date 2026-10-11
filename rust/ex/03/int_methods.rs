fn main() {
    let a: i32 = -7;
    let b: i32 = 3;
    println!("2 의 10 제곱   {}", 2_i32.pow(10));
    println!("절댓값         {}", a.abs());
    println!("작은 쪽·큰 쪽  {} {}", a.min(b), a.max(b));
    println!("두 수의 거리   {}", a.abs_diff(b));
    println!("17 의 제곱근   {}", 17_i32.isqrt());
    // 비트를 세는 메서드 — 0b0010_1100 은 44 다
    let bits: u8 = 0b0010_1100;
    println!("1 인 비트      {}", bits.count_ones());
    println!("앞쪽의 0       {}", bits.leading_zeros());
    println!("뒤쪽의 0       {}", bits.trailing_zeros());
}
