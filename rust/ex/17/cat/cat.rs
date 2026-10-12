use std::env;
use std::fs::File;
use std::io::{self, Write};
use std::process::ExitCode;

// 파일 하나를 열어 out 으로 끝까지 옮긴다
fn cat(path: &str, out: &mut impl Write) -> io::Result<()> {
    let mut file = File::open(path)?;
    io::copy(&mut file, out)?;
    Ok(())
}

fn main() -> ExitCode {
    let mut out = io::stdout().lock();
    let mut failed = false;
    for path in env::args().skip(1) {
        // 이름은 아는 쪽이 붙인다. 실패해도 다음 파일로 간다
        if let Err(e) = cat(&path, &mut out) {
            eprintln!("cat: {path}: {e}");
            failed = true;
        }
    }
    if failed {
        ExitCode::FAILURE
    } else {
        ExitCode::SUCCESS
    }
}
