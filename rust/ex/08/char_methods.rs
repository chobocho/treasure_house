fn main() {
    for c in ['a', 'Z', '7', '가', ' ', '!'] {
        println!(
            "{c:?} 글자:{} 숫자:{} 공백:{} 대문자:{}",
            c.is_alphabetic(),
            c.is_ascii_digit(),
            c.is_whitespace(),
            c.is_uppercase()
        );
    }
    println!("{:?} {:?}", '7'.to_digit(10), 'f'.to_digit(16));
    println!("{} {}", 'a' as u32, char::from(65u8));
}
