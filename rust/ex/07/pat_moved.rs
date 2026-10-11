#[derive(Debug)]
enum Message {
    Text(String),
    Quit,
}

fn main() {
    let msg = Message::Text(String::from("안녕"));

    match msg {
        Message::Text(s) => println!("{s}"),
        Message::Quit => println!("끝"),
    }
    println!("{msg:?}");
}
//@ expect: E0382
