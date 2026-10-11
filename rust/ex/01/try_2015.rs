use std::num::ParseIntError;

// 1.13 전에는 오류를 위로 넘길 때 try! 매크로를 썼다.
fn double(s: &str) -> Result<i32, ParseIntError> {
    let n = try!(s.parse::<i32>());
    Ok(n * 2)
}

fn main() {
    println!("{:?}", double("21"));
    println!("{:?}", double("x"));
}
//@ edition: 2015
//@ warnings: show
