use std::io;
use std::process::ExitCode;

fn run() -> Result<i64, String> {
    let mut total = 0;
    // enumerate 는 0 부터 센다 — 1 을 더해 줄 번호로 쓴다
    for (i, line) in io::stdin().lines().enumerate() {
        let line = line.map_err(|e| e.to_string())?;
        let n: i64 = line
            .trim()
            .parse()
            .map_err(|e| format!("{}번째 줄 {line:?}: {e}", i + 1))?;
        total += n;
    }
    Ok(total)
}

fn main() -> ExitCode {
    match run() {
        Ok(total) => {
            println!("합계 {total}");
            ExitCode::SUCCESS
        }
        Err(msg) => {
            eprintln!("sum: {msg}");
            ExitCode::from(2)
        }
    }
}
//@ stdin: 10\n이십\n30\n
//@ exit: 2
