fn main() {
    let c = 'r';
    println!("글자인가     {}", c.is_alphabetic());
    println!("'가' 도 글자 {}", '가'.is_alphabetic());
    println!("숫자인가     {}", c.is_ascii_digit());
    println!("'7' 은 숫자  {}", '7'.is_ascii_digit());
    println!("공백인가     {}", ' '.is_whitespace());
    println!("대문자로     {}", c.to_ascii_uppercase());
    // 이름에 ascii 가 들면 ASCII 범위의 글자만 본다
    println!("'가' 는 ASCII 글자 {}", '가'.is_ascii_alphabetic());
    println!("'가' 를 대문자로   {}", '가'.to_ascii_uppercase());
    // 숫자 글자를 수로 — 인자는 진법이다
    println!("'7' 을 10진법으로 {:?}", '7'.to_digit(10));
    println!("'f' 를 16진법으로 {:?}", 'f'.to_digit(16));
    println!("'f' 를 10진법으로 {:?}", 'f'.to_digit(10));
}
