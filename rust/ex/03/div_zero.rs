use std::env;

fn main() {
    let args: Vec<String> = env::args().collect();
    let people: i32 = args[1].parse().expect("수가 아니다");
    // checked_div 는 나눌 수 없으면 None 을 준다
    println!("{:?}", 100_i32.checked_div(people));
    println!("{}", 100 / people);
}
//@ args: 0
//@ flags: -O
//@ exit: 101
