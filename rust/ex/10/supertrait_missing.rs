use std::fmt::Display;

trait Named: Display {
    fn name(&self) -> String;
}

struct Port(u16);

impl Named for Port {
    fn name(&self) -> String {
        format!("포트 {}", self.0)
    }
}

fn main() {
    println!("{}", Port(8080).0);
}
//@ expect: E0277
