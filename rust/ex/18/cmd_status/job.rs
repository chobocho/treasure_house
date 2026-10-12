use std::env;
use std::process::ExitCode;

fn main() -> ExitCode {
    // 첫 인자로 받은 수를 종료 코드로 쓴다
    let arg = env::args().nth(1).unwrap_or_default();
    let code: u8 = arg.parse().unwrap_or(0);
    println!("  job: 일을 했다. 종료 코드 {code}");
    ExitCode::from(code)
}
