use std::io;

fn main() {
    // 읽은 글자를 담을 빈 문자열
    let mut line = String::new();
    // 한 줄을 읽어 line 에 붙이고, 읽은 바이트 수를 돌려준다
    let n = io::stdin().read_line(&mut line).expect("읽기 실패");
    println!("{n} 바이트를 읽었다");
    // 엔터로 들어온 줄바꿈까지 들어 있다
    println!("{line:?}");
}
//@ stdin: 21\n
