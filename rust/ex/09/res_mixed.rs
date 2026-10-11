use std::num::ParseIntError;

fn ratio(a: &str, b: &str) -> Result<f64, ParseIntError> {
    let x = a.parse::<i32>()?;
    let y = b.parse::<f64>()?; // 이 줄의 오류는 ParseFloatError 다
    Ok(x as f64 / y)
}

fn main() {
    println!("{:?}", ratio("1", "2.0"));
}
//@ expect: E0277
