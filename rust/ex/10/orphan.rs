use std::fmt;

// 남의 트레이트(Display)를 남의 타입(Vec)에 구현하려 한다.
impl fmt::Display for Vec<i32> {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "{}개", self.len())
    }
}

fn main() {
    println!("{}", vec![1, 2, 3]);
}
//@ expect: E0117
