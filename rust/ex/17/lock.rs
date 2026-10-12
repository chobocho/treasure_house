use std::io::{self, Write};
use std::thread;

fn main() -> io::Result<()> {
    // 열쇠를 쥔 동안 표준 출력은 이 스레드만 쓴다
    let mut out = io::stdout().lock();
    let other = thread::spawn(|| println!("다른 스레드: 기다렸다"));
    for i in 1..=3 {
        writeln!(out, "main: {i}번 줄")?;
    }
    // 열쇠를 놓아야 다른 스레드가 찍을 수 있다
    drop(out);
    other.join().unwrap();
    Ok(())
}
