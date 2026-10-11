use std::io;

fn main() {
    let mut line = String::new();
    io::stdin().read_line(&mut line).expect("읽기 실패");
    // 줄바꿈이 붙은 채로 정수로 바꾸려 한다
    let n: i32 = line.parse().expect("숫자가 아니다");
    println!("{n} 의 두 배는 {}", n * 2);
}
//@ stdin: 21\n
//@ exit: 101
