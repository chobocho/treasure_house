// 함수 포인터로 받는다.
fn apply(f: fn(i32) -> i32, x: i32) -> i32 {
    f(x)
}

fn double(x: i32) -> i32 {
    x * 2
}

fn main() {
    let offset = 10;
    println!("{}", apply(double, 5));
    // 붙잡은 것이 없는 클로저
    println!("{}", apply(|x| x + 1, 5));
    // offset 을 붙잡은 클로저
    println!("{}", apply(|x| x + offset, 5));
}
//@ expect: E0308
