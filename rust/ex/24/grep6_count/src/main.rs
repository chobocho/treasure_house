use std::env;
use std::io;
use std::process::ExitCode;

fn main() -> ExitCode {
    let args: Vec<String> = env::args().skip(1).collect();
    let mut out = io::stdout();
    let mut err = io::stderr();
    match grep::run(&args, io::stdin(), &mut out, &mut err) {
        Ok(code) => ExitCode::from(code),
        Err(e) => {
            // 표준 입력을 읽거나 결과를 쓰다가 실패했다.
            // 1 은 "고른 줄이 없다" 라서 2 로 끝낸다
            eprintln!("grep: {e}");
            ExitCode::from(2)
        }
    }
}
