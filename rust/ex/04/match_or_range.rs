fn kind(c: char) -> &'static str {
    match c {
        'a' | 'e' | 'i' | 'o' | 'u' => "모음",
        'a'..='z' => "자음",
        '0'..='9' => "숫자",
        _ => "그 밖",
    }
}

fn main() {
    println!("{} {} {} {}", kind('e'), kind('k'), kind('7'), kind('!'));
}
