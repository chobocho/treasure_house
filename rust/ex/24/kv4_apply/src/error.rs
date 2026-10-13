use std::fmt;
use std::io;

// 저장소가 일을 하지 못한 까닭
#[derive(Debug)]
pub enum KvError {
    // 읽거나 쓰는 일이 실패했다
    Io(io::Error),
}

impl fmt::Display for KvError {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        match self {
            KvError::Io(e) => write!(f, "{e}"),
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
