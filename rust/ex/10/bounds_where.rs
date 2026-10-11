use std::fmt::{Debug, Display};

// 조건이 여럿이면 + 로 잇는다.
fn show<T: Display + PartialOrd>(a: T, b: T) {
    println!("{}", if a > b { a } else { b });
}

// 길어지면 where 로 뺀다 — 시그니처의 첫 줄이 읽기 쉬워진다.
fn report<K, V>(key: K, value: V) -> String
where
    K: Display,
    V: Debug + Clone,
{
    format!("{key} = {:?}", value.clone())
}

fn main() {
    show(3, 8);
    println!("{}", report("ports", vec![80, 443]));
}
