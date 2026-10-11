use std::error::Error;
use std::fmt;
use std::num::ParseIntError;

#[derive(Debug)]
struct LineError {
    line: usize,
    cause: ParseIntError,
}

impl fmt::Display for LineError {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "{}번째 줄을 읽지 못했다", self.line)
    }
}

impl Error for LineError {
    // 이 오류를 낳은 더 아래의 오류.
    fn source(&self) -> Option<&(dyn Error + 'static)> {
        Some(&self.cause)
    }
}

fn main() {
    let cause = "x1".parse::<i32>().unwrap_err();
    let e = LineError { line: 3, cause };
    println!("{e}");
    if let Some(inner) = e.source() {
        println!("  까닭: {inner}");
    }
}
