// 'a — "돌려주는 참조는 a 와 b 가 둘 다 살아 있는 동안만 쓸 수 있다".
fn longest<'a>(a: &'a str, b: &'a str) -> &'a str {
    if a.len() >= b.len() { a } else { b }
}

fn main() {
    let x = String::from("apple");
    let y = String::from("fig");
    let winner = longest(&x, &y);
    println!("{winner}");
}
