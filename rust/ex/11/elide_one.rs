// 들어오는 참조가 하나면, 나가는 참조의 수명은 그것으로 정해진다.
fn first_word(text: &str) -> &str {
    text.split(' ').next().unwrap_or("")
}

// 위와 똑같은 뜻 — 컴파일러가 채워 주는 것을 손으로 쓴 모양.
fn first_word_explicit<'a>(text: &'a str) -> &'a str {
    text.split(' ').next().unwrap_or("")
}

fn main() {
    let s = String::from("hello rust world");
    println!("{} {}", first_word(&s), first_word_explicit(&s));
}
