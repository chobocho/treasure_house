use std::env;
use std::io;
use std::process::ExitCode;

fn main() -> ExitCode {
    let args: Vec<String> = env::args().skip(1).collect();
    let mut out = io::stdout();
    let mut err = io::stderr();
    match calc::run(&args, io::stdin(), &mut out, &mut err) {
        Ok(code) => ExitCode::from(code),
        Err(e) => {
            // 표준 입력을 읽거나 답을 쓰다가 실패했다.
            // 1 은 "오류인 줄이 있었다" 라서 2 로 끝낸다
            eprintln!("calc: {e}");
            ExitCode::from(2)
        }
    }
}
