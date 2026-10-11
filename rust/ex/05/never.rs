// 돌아오지 않는 함수의 반환 타입은 ! 이다.
fn fail(msg: &str) -> ! {
    eprintln!("오류: {msg}");
    std::process::exit(2);
}

fn parse(s: &str) -> i32 {
    match s.parse() {
        Ok(n) => n,
        // ! 는 어떤 타입 자리에도 맞는다
        Err(_) => fail("숫자가 아니다"),
    }
}

fn main() {
    println!("{}", parse("42"));
    println!("{}", parse("사십이"));
}
//@ exit: 2
