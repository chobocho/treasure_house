// 5장의 first_word 에서 매개변수만 &str 로 바꿨다
fn first_word(s: &str) -> &str {
    let bytes = s.as_bytes();
    for i in 0..bytes.len() {
        if bytes[i] == b' ' {
            return &s[..i];
        }
    }
    s
}

fn main() {
    let owned = String::from("hello world");

    // 리터럴
    println!("[{}]", first_word("good morning"));
    // String 을 빌린 것
    println!("[{}]", first_word(&owned));
    // String 의 한 구간
    println!("[{}]", first_word(&owned[6..]));
}
