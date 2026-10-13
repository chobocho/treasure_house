use std::fmt;
use std::io;

use crate::format::LineError;

// 저장소가 일을 하지 못한 까닭
#[derive(Debug)]
pub enum KvError {
    // 읽거나 쓰는 일이 실패했다
    Io(io::Error),
    // 파일을 읽거나 쓰지 못했다 — 파일 이름과 까닭
    File(String, io::Error),
    // 저장소 파일의 한 줄이 항목이 아니다 — 이름, 줄 번호, 까닭
    Corrupt(String, usize, LineError),
}

impl fmt::Display for KvError {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        match self {
            KvError::Io(e) => write!(f, "{e}"),
            KvError::File(name, e) => write!(f, "{name}: {e}"),
            KvError::Corrupt(name, line, why) => {
                write!(f, "{name} {line}번째 줄: {why}")
            }
        }
    }
}

impl std::error::Error for KvError {}

// ? 가 io::Error 를 만나면 이것으로 바꾼다
impl From<io::Error> for KvError {
    fn from(e: io::Error) -> Self {
        KvError::Io(e)
    }
}
