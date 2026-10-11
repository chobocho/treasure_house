use std::any::type_name_of_val;

fn main() {
    // 소수점이 있는 리터럴은 단서가 없으면 f64 다
    let a = 1.0 / 3.0;
    // 타입 표기나 접미사로 f32 를 고른다
    let b: f32 = 1.0 / 3.0;
    let c = 2.5_f32;
    println!("a = {a} ({})", type_name_of_val(&a));
    println!("b = {b} ({})", type_name_of_val(&b));
    println!("c = {c} ({})", type_name_of_val(&c));
    // 1e3 은 1 × 10³ — 지수 표기도 실수 리터럴이다
    println!("1e3 = {}, 2.5e-3 = {}", 1e3, 2.5e-3);
    println!("f32 의 끝 = {:e}", f32::MAX);
    println!("f64 의 끝 = {:e}", f64::MAX);
}
