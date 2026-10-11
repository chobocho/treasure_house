// 첫 낱말을 가리키는 슬라이스를 돌려준다
fn first_word(s: &String) -> &str {
    let bytes = s.as_bytes();
    for i in 0..bytes.len() {
        if bytes[i] == b' ' {
            return &s[..i];
        }
    }
    &s[..]
}

fn main() {
    let s = String::from("hello world");
    let word = first_word(&s);
    println!("[{word}] {}바이트", word.len());

    let one = String::from("rust");
    println!("[{}]", first_word(&one));
}
