use std::io::{self, Write};

fn main() {
    let mut out = io::stdout();
    loop {
        // writeln! 은 실패를 Result 로 돌려준다
        if let Err(e) = writeln!(out, "y") {
            eprintln!("그만 찍는다: {e}");
            break;
        }
    }
}
