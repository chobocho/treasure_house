use std::num::ParseIntError;

fn double(s: &str) -> Result<i32, ParseIntError> {
    let n = try!(s.parse::<i32>());
    Ok(n * 2)
}

fn main() {
    println!("{:?}", double("21"));
}
//@ expect: error
