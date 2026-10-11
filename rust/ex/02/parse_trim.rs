use std::io;

fn main() {
    let mut line = String::new();
    io::stdin().read_line(&mut line).expect("읽기 실패");
    // trim 이 앞뒤의 공백과 줄바꿈을 떼어 낸다
    let n: i32 = line.trim().parse().expect("숫자가 아니다");
    println!("{n} 의 두 배는 {}", n * 2);
}
//@ stdin: 21\n
