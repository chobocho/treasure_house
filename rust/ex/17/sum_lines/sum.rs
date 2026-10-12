use std::error::Error;
use std::io;

fn main() -> Result<(), Box<dyn Error>> {
    let mut total = 0;
    for line in io::stdin().lines() {
        // 첫 ? 는 io::Error 를, 둘째 ? 는 ParseIntError 를 올려 보낸다
        let n: i64 = line?.trim().parse()?;
        total += n;
    }
    println!("합계 {total}");
    Ok(())
}
