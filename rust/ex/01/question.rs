use std::num::ParseIntError;

// 지금의 모양 — try!(식) 대신 식 뒤에 ? 하나.
fn double(s: &str) -> Result<i32, ParseIntError> {
    let n = s.parse::<i32>()?;
    Ok(n * 2)
}

fn main() {
    println!("{:?}", double("21"));
    println!("{:?}", double("x"));
}
