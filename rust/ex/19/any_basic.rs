use std::any::{Any, TypeId};

// 무엇이든 받는다. 아는 타입이면 속을 꺼내 쓴다.
fn describe(value: &dyn Any) -> String {
    if let Some(n) = value.downcast_ref::<i32>() {
        format!("정수 {n}")
    } else if let Some(s) = value.downcast_ref::<String>() {
        format!("글 {s:?}, {} 바이트", s.len())
    } else {
        String::from("모르는 타입")
    }
}

fn main() {
    println!("{}", describe(&42));
    println!("{}", describe(&String::from("hi")));
    println!("{}", describe(&2.5));
    // &str 은 String 이 아니다.
    println!("{}", describe(&"hi"));

    let value: &dyn Any = &42;
    println!("{} {}", value.is::<i32>(), value.is::<i64>());
    println!("{:?}", value.downcast_ref::<i64>());
    // TypeId 는 찍지 않고 견주기만 한다.
    println!("{}", value.type_id() == TypeId::of::<i32>());
}
