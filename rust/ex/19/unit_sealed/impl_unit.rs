// impl_unit.rs — 밖에서 Unit 을 구현해 본다
use units::Unit;

struct Mile;

impl Unit for Mile {
    fn index(&self) -> usize {
        2
    }
}

fn main() {
    println!("{}", units::name(&Mile));
}
