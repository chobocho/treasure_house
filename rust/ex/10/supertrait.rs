use std::fmt::Display;

// Named 를 구현하려면 Display 도 구현해야 한다(상위 트레이트).
trait Named: Display {
    fn name(&self) -> String;

    fn banner(&self) -> String {
        // 그래서 여기서 {} 로 찍을 수 있다.
        format!("== {} ({}) ==", self.name(), self)
    }
}

struct Port(u16);

impl Display for Port {
    fn fmt(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {
        write!(f, ":{}", self.0)
    }
}

impl Named for Port {
    fn name(&self) -> String {
        String::from("포트")
    }
}

fn main() {
    println!("{}", Port(8080).banner());
}
