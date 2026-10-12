use std::env;
use std::process::ExitCode;

fn main() -> ExitCode {
    // 0번 인자(프로그램 자신)는 뺀다.
    let args: Vec<String> = env::args().skip(1).collect();
    match shout::run(&args) {
        Ok(text) => {
            println!("{text}");
            ExitCode::SUCCESS
        }
        Err(usage) => {
            eprintln!("{usage}");
            ExitCode::from(2)
        }
    }
}
