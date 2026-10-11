struct Words<'a> {
    text: &'a str,
}

// '_ — "수명이 있지만 이름은 붙이지 않겠다".
fn make(text: &str) -> Words<'_> {
    Words { text }
}

fn main() {
    let s = String::from("hello rust");
    let w = make(&s);
    println!("{}", w.text);
}
