trait Animal {
    // self 가 없는 함수도 트레이트에 넣을 수 있다.
    fn new(name: &str) -> Self;
    fn speak(&self) -> String;
}

struct Dog(String);
struct Cat(String);

impl Animal for Dog {
    fn new(name: &str) -> Self {
        Dog(name.to_string())
    }
    fn speak(&self) -> String {
        format!("{}: 멍", self.0)
    }
}

impl Animal for Cat {
    fn new(name: &str) -> Self {
        Cat(name.to_string())
    }
    fn speak(&self) -> String {
        format!("{}: 야옹", self.0)
    }
}

fn introduce<A: Animal>(name: &str) -> String {
    A::new(name).speak()
}

fn main() {
    println!("{}", introduce::<Dog>("바둑이"));
    println!("{}", introduce::<Cat>("나비"));
}
