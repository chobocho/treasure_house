use std::env;

fn main() {
    let scores = [70, 85, 90];
    // 번호를 실행할 때 받는다 — 컴파일러는 미리 알 수 없다
    let args: Vec<String> = env::args().collect();
    let i: usize = args[1].parse().expect("수가 아니다");
    // get 은 그 칸이 있는지를 함께 알려 준다
    println!("{:?}", scores.get(1));
    println!("{:?}", scores.get(i));
    // 대괄호는 칸이 없으면 패닉한다
    println!("{}", scores[i]);
    println!("여기까지 오지 못한다");
}
//@ args: 3
//@ exit: 101
