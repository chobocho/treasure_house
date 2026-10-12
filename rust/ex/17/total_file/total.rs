use std::error::Error;
use std::fs::File;
use std::io::{BufRead, BufReader};

// 2장의 total 그대로다
fn total(input: impl BufRead) -> Result<i64, Box<dyn Error>> {
    let mut sum = 0;
    for line in input.lines() {
        sum += line?.trim().parse::<i64>()?;
    }
    Ok(sum)
}

fn main() -> Result<(), Box<dyn Error>> {
    // 이번에는 표준 입력이 아니라 파일을 넘겨준다
    let file = File::open("numbers.txt")?;
    let sum = total(BufReader::new(file))?;
    println!("합계 {sum}");
    Ok(())
}
