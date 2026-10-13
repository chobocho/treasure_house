use std::fmt;

#[derive(Debug)]
struct Empty;

impl fmt::Display for Empty {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "빈 입력")
    }
}

// Display 는 구현했다 — Debug 는 없다
impl std::error::Error for Empty {}

fn main() {
    println!("{}", Empty);
}
