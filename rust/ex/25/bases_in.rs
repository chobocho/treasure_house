use std::io;

fn main() {
    let mut line = String::new();
    io::stdin().read_line(&mut line).expect("읽기 실패");
    let n: i32 = line.trim().parse().expect("숫자가 아니다");
    println!("dec {n:12}");
    println!("hex {n:#12x}");
    println!("oct {n:#12o}");
    println!("bin {n:#12b}");
    println!("bit {n:012b}");
}
//@ stdin: 202\n
