// impl Fn(i32) -> i32 — "i32 를 받아 i32 를 내는, 부를 수 있는 것".
fn apply_twice(f: impl Fn(i32) -> i32, x: i32) -> i32 {
    f(f(x))
}

fn double(x: i32) -> i32 {
    x * 2
}

fn main() {
    let offset = 3;
    println!("{}", apply_twice(|x| x + offset, 10)); // 클로저
    println!("{}", apply_twice(double, 10)); // 보통 함수도 된다
}
