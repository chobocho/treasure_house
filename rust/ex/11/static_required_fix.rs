fn keep_forever(text: &str) {
    println!("{text}");
}

fn main() {
    keep_forever("리터럴은 된다");
    let s = String::from("지역 변수");
    keep_forever(&s);
}
