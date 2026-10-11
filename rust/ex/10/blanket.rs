use std::fmt::Display;

trait Shout {
    fn shout(&self) -> String;
}

// 포괄 구현 — Display 인 모든 타입에 한꺼번에.
impl<T: Display> Shout for T {
    fn shout(&self) -> String {
        format!("{}!", self.to_string().to_uppercase())
    }
}

fn main() {
    println!("{}", "hello".shout());
    println!("{}", 42.shout());
    println!("{}", 'x'.shout());
}
