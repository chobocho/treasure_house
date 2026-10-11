use std::any::type_name_of_val;

fn main() {
    let order: i32 = 3;
    // 타입::from(값) — 만들 타입을 앞에 적는다
    let a = i64::from(order);
    // 값.into() — 받는 쪽의 타입 표기를 보고 정한다
    let b: i64 = order.into();
    println!("a = {a} ({})", type_name_of_val(&a));
    println!("b = {b} ({})", type_name_of_val(&b));
    // 2장에서 막혔던 견주기
    let stock: i64 = 1000;
    println!("{}", stock > order.into());
    // 정수 → 실수, 글자 → 번호, bool → 수 도 잃을 것이 없다
    println!("{:?}", f64::from(order));
    println!("{}", u32::from('a'));
    println!("{}", i32::from(true));
}
