// impl_sealed.rs — 밖에서 Sealed 부터 구현해 본다
use units::Unit;

struct Mile;

impl units::sealed::Sealed for Mile {}

impl Unit for Mile {
    fn index(&self) -> usize {
        2
    }
}

fn main() {
    println!("{}", units::name(&Mile));
}
