use std::error::Error;
use std::io;

fn main() -> Result<(), Box<dyn Error>> {
    let mut count = 0;
    let mut total = 0;
    for line in io::stdin().lines() {
        let line = line?;
        // 둘째 칸이 없는 줄은 건너뛴다 — 빈 줄이 그렇다
        let Some(score) = line.split_whitespace().nth(1) else {
            continue;
        };
        total += score.parse::<u32>()?;
        count += 1;
    }
    println!("{count}명, 합계 {total}");
    Ok(())
}
//@ stdin: kim 90\nlee 85\n\npark 77\n
