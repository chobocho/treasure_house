use std::error::Error;
use std::io::{self, BufRead};

// 줄 단위로 읽을 수 있는 것이면 무엇이든 받는다
fn total(input: impl BufRead) -> Result<i64, Box<dyn Error>> {
    let mut sum = 0;
    for line in input.lines() {
        sum += line?.trim().parse::<i64>()?;
    }
    Ok(sum)
}

fn main() -> Result<(), Box<dyn Error>> {
    // lock() 이 내준 열쇠가 BufRead 를 구현한다
    let sum = total(io::stdin().lock())?;
    println!("합계 {sum}");
    Ok(())
}
