use std::num::ParseIntError;

fn double(s: &str) -> Result<i32, ParseIntError> {
    Ok(s.parse::<i32>()? * 2)
}

// 시험도 Result 를 돌려줄 수 있다 — ? 를 쓸 수 있고, Err 면 실패다.
#[test]
fn doubles() -> Result<(), ParseIntError> {
    assert_eq!(double("21")?, 42);
    Ok(())
}
//@ test
