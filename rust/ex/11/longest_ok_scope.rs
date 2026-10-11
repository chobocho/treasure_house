fn longest<'a>(a: &'a str, b: &'a str) -> &'a str {
    if a.len() >= b.len() { a } else { b }
}

fn main() {
    let x = String::from("apple");
    {
        let y = String::from("fig");
        // 결과를 y 가 살아 있는 동안에만 쓴다 — 괜찮다.
        let winner = longest(&x, &y);
        println!("{winner}");
    }
    println!("{x}");
}
