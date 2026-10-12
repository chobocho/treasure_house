use std::fmt::Debug;

// 타입 인자에 이름이 있다.
fn show<T: Debug>(x: Option<T>) {
    match x {
        Some(v) => println!("{v:?}"),
        None => println!("없음"),
    }
}

fn main() {
    show(Some(3));
    show::<i32>(None);
    show(None::<&str>);
}
