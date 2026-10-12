use std::fs;
use std::process::ExitCode;

fn read(path: &str) -> Result<String, String> {
    // io::Error 는 파일 이름을 모른다 — 아는 쪽이 붙인다
    fs::read_to_string(path).map_err(|e| format!("{path}: {e}"))
}

fn main() -> ExitCode {
    for path in ["a.txt", "b.txt"] {
        match read(path) {
            Ok(text) => println!("{path}: {} 바이트", text.len()),
            Err(msg) => {
                eprintln!("{msg}");
                return ExitCode::FAILURE;
            }
        }
    }
    ExitCode::SUCCESS
}
