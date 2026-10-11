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

// 일부러 실패시킨다 — "x" 는 수가 아니라서 ? 가 Err 를 돌려준다.
#[test]
fn doubles_x() -> Result<(), ParseIntError> {
    assert_eq!(double("x")?, 0);
    Ok(())
}
//@ test
//@ args: --test-threads=1
//@ exit: 101
