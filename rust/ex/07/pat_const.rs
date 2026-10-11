const MAX: u32 = 100;

fn check(n: u32) -> &'static str {
    match n {
        0 => "없음",
        MAX => "가득", // 상수도 패턴이 된다
        1..MAX => "보통",
        _ => "넘침",
    }
}

fn main() {
    println!(
        "{} {} {} {}",
        check(0),
        check(50),
        check(100),
        check(101)
    );
}
