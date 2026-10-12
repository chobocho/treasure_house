// main.rs — units 를 가져다 쓰는 크레이트
use units::{Foot, Meter, Unit};

struct Mile;

// 라이브러리가 모르는 구현이 하나 늘었다.
impl Unit for Mile {
    fn index(&self) -> usize {
        2
    }
}

fn main() {
    println!("{} {}", units::name(&Meter), units::name(&Foot));
    println!("{}", units::name(&Mile));
}
