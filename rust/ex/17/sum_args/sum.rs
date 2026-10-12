use std::env;
use std::process::ExitCode;

// 일은 run 이 하고, 실패는 Result 로 올려 보낸다
fn run() -> Result<i64, String> {
    let mut total = 0;
    for arg in env::args().skip(1) {
        let n: i64 =
            arg.parse().map_err(|e| format!("`{arg}`: {e}"))?;
        total += n;
    }
    Ok(total)
}

// main 은 어디에 찍고 몇 번으로 끝낼지만 정한다
fn main() -> ExitCode {
    match run() {
        Ok(total) => {
            println!("{total}");
            ExitCode::SUCCESS
        }
        Err(msg) => {
            eprintln!("sum: {msg}");
            ExitCode::from(2)
        }
    }
}
