use std::fmt::Debug;

fn show(x: Option<impl Debug>) {
    match x {
        Some(v) => println!("{v:?}"),
        None => println!("없음"),
    }
}

fn main() {
    show(Some(3));
    // None 에 타입을 직접 적어 주려 했다.
    show::<i32>(None);
}
//@ expect: E0107
