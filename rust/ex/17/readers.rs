use std::error::Error;
use std::io::{BufRead, Cursor};

// 2장과 3장의 total 그대로다
fn total(input: impl BufRead) -> Result<i64, Box<dyn Error>> {
    let mut sum = 0;
    for line in input.lines() {
        sum += line?.trim().parse::<i64>()?;
    }
    Ok(sum)
}

fn main() -> Result<(), Box<dyn Error>> {
    // 바이트 슬라이스 &[u8] 는 BufRead 다
    println!("{}", total("10\n20\n30\n".as_bytes())?);

    // Cursor 는 가진 데이터를 감싸 BufRead 로 만든다
    let owned = String::from("100\n200\n");
    println!("{}", total(Cursor::new(owned))?);

    // Cursor 는 어디까지 읽었는지를 기억한다
    let mut cur = Cursor::new(String::from("7\n8\n"));
    let mut line = String::new();
    cur.read_line(&mut line)?;
    println!("{line:?} 을 읽었고 자리는 {}", cur.position());
    println!("{}", total(cur)?);
    Ok(())
}
