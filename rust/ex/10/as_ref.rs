// AsRef<str> — "&str 로 볼 수 있는 것이면 무엇이든".
fn shout(text: impl AsRef<str>) -> String {
    text.as_ref().to_uppercase()
}

fn main() {
    println!("{}", shout("literal"));
    println!("{}", shout(String::from("owned")));
    println!("{}", shout(&String::from("borrowed")));
}
