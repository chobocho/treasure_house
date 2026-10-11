use std::any::type_name_of_val;

fn main() {
    // 단서가 없으면 i32
    let a = 42;
    // 접미사가 단서다
    let b = 42u8;
    // 뒤에서 i64 자리에 쓰인 것이 단서다 — c 도 i64 가 된다
    let c = 42;
    let d: i64 = c;

    println!("a: {}", type_name_of_val(&a));
    println!("b: {}", type_name_of_val(&b));
    println!("c: {}", type_name_of_val(&c));
    println!("d: {}", type_name_of_val(&d));
}
