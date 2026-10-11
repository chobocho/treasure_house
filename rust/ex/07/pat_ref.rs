#[derive(Debug)]
enum Message {
    Text(String),
    Quit,
}

fn main() {
    let msg = Message::Text(String::from("안녕"));

    // 참조를 match 하면, 꺼낸 것도 참조다 — 아무것도 옮겨 가지 않는다.
    match &msg {
        Message::Text(s) => println!("글자 수 {}", s.chars().count()),
        Message::Quit => println!("끝"),
    }
    println!("{msg:?}"); // 그래서 여전히 쓸 수 있다
    println!("{:?}", Message::Quit);
}
