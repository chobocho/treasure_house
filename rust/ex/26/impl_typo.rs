trait Greet {
    fn hello(&self) -> String {
        String::from("안녕")
    }
}

struct Cat;

impl Greet for Cat {
    fn hello(&self) -> String {
        String::from("야옹")
    }
}

fn main() {
    println!("{}", Cat.hello());
}
