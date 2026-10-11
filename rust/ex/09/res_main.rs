use std::num::ParseIntError;

// main 도 Result 를 돌려줄 수 있다.
fn main() -> Result<(), ParseIntError> {
    let a = "42".parse::<i32>()?;
    println!("{a}");
    let b = "사십이".parse::<i32>()?;
    println!("{b}");
    Ok(())
}
//@ exit: 1
