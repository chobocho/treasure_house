use std::fmt;

#[derive(Debug)]
enum ConfigError {
    Missing(String),
    BadNumber(String),
}

// Display 를 구현하면 {} 로 사람이 읽을 말을 찍을 수 있다.
impl fmt::Display for ConfigError {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        match self {
            ConfigError::Missing(k) => write!(f, "{k} 항목이 없다"),
            ConfigError::BadNumber(v) => {
                write!(f, "숫자가 아니다: {v}")
            }
        }
    }
}

// 본문 없이도 된다 — "이 타입은 오류다" 라는 표시.
impl std::error::Error for ConfigError {}

fn main() {
    let e = ConfigError::BadNumber(String::from("abc"));
    println!("{e}"); // Display — 사용자에게 보일 말
    println!("{e:?}"); // Debug — 개발자가 볼 모양
    println!("{}", ConfigError::Missing(String::from("port")));
}
