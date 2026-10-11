fn main() {
    let s = String::from("hello world");

    // 0번 바이트부터 5번 바이트 앞까지
    let hello = &s[0..5];
    let world = &s[6..11];
    println!("[{hello}] [{world}]");

    // 처음과 끝은 생략할 수 있다
    println!("[{}] [{}]", &s[..5], &s[6..]);
    println!("[{}]", &s[..]);

    // 슬라이스의 타입은 &str 이다
    let part: &str = &s[3..8];
    println!("[{part}] {}바이트", part.len());
}
