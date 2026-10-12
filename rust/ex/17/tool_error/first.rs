use std::env;
use std::error::Error;
use std::fmt;
use std::fs;
use std::io::{self, ErrorKind, Write};
use std::process::ExitCode;

// 이 도구가 낼 수 있는 실패
#[derive(Debug)]
enum ToolError {
    // 파일을 다루다 난 실패 — 이름을 함께 담는다
    File { path: String, source: io::Error },
    // 이름이 없는 실패 — 표준 출력에 쓰다 난 것
    Io(io::Error),
}

impl fmt::Display for ToolError {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        match self {
            ToolError::File { path, source } => {
                write!(f, "{path}: {source}")
            }
            ToolError::Io(e) => write!(f, "{e}"),
        }
    }
}

impl Error for ToolError {}

// ? 가 io::Error 를 만나면 이것을 불러 Io 로 바꾼다
impl From<io::Error> for ToolError {
    fn from(e: io::Error) -> Self {
        ToolError::Io(e)
    }
}

// 파일의 첫 줄을 이름과 함께 out 에 쓴다
fn first_line(
    path: &str,
    out: &mut impl Write,
) -> Result<(), ToolError> {
    // 이름을 아는 자리다 — map_err 로 오류에 이름을 싣는다
    let text =
        fs::read_to_string(path).map_err(|source| ToolError::File {
            path: path.to_string(),
            source,
        })?;
    let line = text.lines().next().unwrap_or("");
    // 이름이 없는 실패는 From 이 Io 로 바꾼다
    writeln!(out, "{path}: {line}")?;
    Ok(())
}

fn main() -> ExitCode {
    let mut out = io::stdout().lock();
    for path in env::args().skip(1) {
        match first_line(&path, &mut out) {
            Ok(()) => {}
            // 오류가 글이 아니라 값이라서 종류를 물을 수 있다
            Err(ToolError::File { path, source })
                if source.kind() == ErrorKind::NotFound =>
            {
                eprintln!("first: {path} 가 없어 건너뛴다");
            }
            Err(e) => {
                eprintln!("first: {e}");
                return ExitCode::FAILURE;
            }
        }
    }
    ExitCode::SUCCESS
}
