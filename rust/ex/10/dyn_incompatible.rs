// Self 를 값으로 돌려주는 메서드가 있다.
trait Duplicate {
    fn duplicate(&self) -> Self;
}

struct Stamp(u32);

impl Duplicate for Stamp {
    fn duplicate(&self) -> Self {
        Stamp(self.0)
    }
}

fn main() {
    let items: Vec<Box<dyn Duplicate>> = vec![Box::new(Stamp(1))];
    println!("{}", items.len());
}
//@ expect: E0038
