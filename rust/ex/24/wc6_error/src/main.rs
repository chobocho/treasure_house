use std::env;
use std::io;
use std::process::ExitCode;

fn main() -> ExitCode {
    let args: Vec<String> = env::args().skip(1).collect();
    let mut out = io::stdout();
    let mut err = io::stderr();
    match wc::run(&args, io::stdin(), &mut out, &mut err) {
        Ok(code) => ExitCode::from(code),
        Err(e) => {
            // 표준 입력을 읽거나 결과를 쓰다가 실패했다
            eprintln!("wc: {e}");
            ExitCode::FAILURE
        }
    }
}
