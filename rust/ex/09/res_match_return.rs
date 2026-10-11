use std::num::ParseIntError;

// ? 없이 쓰면 — 실패할 때마다 match 로 받아 직접 돌려보낸다.
fn sum(a: &str, b: &str) -> Result<i32, ParseIntError> {
    let x = match a.parse::<i32>() {
        Ok(n) => n,
        Err(e) => return Err(e),
    };
    let y = match b.parse::<i32>() {
        Ok(n) => n,
        Err(e) => return Err(e),
    };
    Ok(x + y)
}

fn main() {
    println!("{:?}", sum("1", "2"));
    println!("{:?}", sum("1", "둘"));
}
