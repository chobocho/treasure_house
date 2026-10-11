use std::num::ParseIntError;

// 같은 함수 — ? 가 "Err 면 바로 돌려보내기" 를 대신한다.
fn sum(a: &str, b: &str) -> Result<i32, ParseIntError> {
    let x = a.parse::<i32>()?;
    let y = b.parse::<i32>()?;
    Ok(x + y)
}

fn main() {
    println!("{:?}", sum("1", "2"));
    println!("{:?}", sum("1", "둘"));
}
