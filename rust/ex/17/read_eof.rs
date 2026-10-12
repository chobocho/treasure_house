use std::io;

fn main() -> io::Result<()> {
    let mut line = String::new();
    loop {
        // read_line 은 덧붙인다 — 읽기 전에 비운다
        line.clear();
        let n = io::stdin().read_line(&mut line)?;
        println!("{n} 바이트: {line:?}");
        // 0 바이트를 읽었으면 입력이 끝난 것이다
        if n == 0 {
            break;
        }
    }
    Ok(())
}
//@ stdin: kim\n\nlee
