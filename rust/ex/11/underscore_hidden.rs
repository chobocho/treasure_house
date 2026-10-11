struct Words<'a> {
    text: &'a str,
}

// 반환 타입에 수명이 없다 — Words 가 빌린다는 표시가 안 보인다.
fn make(text: &str) -> Words {
    Words { text }
}

fn main() {
    let s = String::from("hello rust");
    let w = make(&s);
    println!("{}", w.text);
}
//@ warnings: show
