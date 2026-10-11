fn longest<'a>(a: &'a str, b: &'a str) -> &'a str {
    if a.len() >= b.len() { a } else { b }
}

fn main() {
    let x = String::from("apple");
    let winner;
    {
        let y = String::from("fig");
        // 결과를 복사해 가지면 y 에 매이지 않는다.
        winner = longest(&x, &y).to_string();
    }
    println!("{winner}");
}
