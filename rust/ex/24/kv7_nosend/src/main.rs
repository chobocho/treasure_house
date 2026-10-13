use std::env;
use std::io;
use std::process::ExitCode;

fn main() -> ExitCode {
    let args: Vec<String> = env::args().skip(1).collect();
    let mut out = io::stdout();
    let mut err = io::stderr();
    match kv::run(&args, io::stdin(), &mut out, &mut err) {
        Ok(code) => ExitCode::from(code),
        Err(e) => {
            // 저장소가 일을 하지 못했거나, 읽고 쓰는 일이 실패했다.
            // 1 은 "알림을 낸 줄이 있었다" 라서 2 로 끝낸다
            eprintln!("kv: {e}");
            ExitCode::from(2)
        }
    }
}
