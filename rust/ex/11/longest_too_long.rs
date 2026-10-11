fn longest<'a>(a: &'a str, b: &'a str) -> &'a str {
    if a.len() >= b.len() { a } else { b }
}

fn main() {
    let x = String::from("apple");
    let winner;
    {
        let y = String::from("fig");
        winner = longest(&x, &y);
    } // y 가 사라진다
    println!("{winner}"); // 결과가 y 일 수도 있었다
}
//@ expect: E0597
