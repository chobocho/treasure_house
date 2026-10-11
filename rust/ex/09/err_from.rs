use std::num::{ParseFloatError, ParseIntError};

#[derive(Debug)]
enum CalcError {
    Int(ParseIntError),
    Float(ParseFloatError),
}

// From 이 있으면 ? 가 알아서 내 오류 타입으로 바꿔 준다.
impl From<ParseIntError> for CalcError {
    fn from(e: ParseIntError) -> Self {
        CalcError::Int(e)
    }
}

impl From<ParseFloatError> for CalcError {
    fn from(e: ParseFloatError) -> Self {
        CalcError::Float(e)
    }
}

fn ratio(a: &str, b: &str) -> Result<f64, CalcError> {
    let x = a.parse::<i32>()?;
    let y = b.parse::<f64>()?;
    Ok(x as f64 / y)
}

fn main() {
    for (a, b) in [("1", "2.0"), ("하나", "2.0"), ("1", "둘")] {
        match ratio(a, b) {
            Ok(v) => println!("{v}"),
            Err(CalcError::Int(e)) => println!("정수 쪽: {e}"),
            Err(CalcError::Float(e)) => println!("실수 쪽: {e}"),
        }
    }
}
