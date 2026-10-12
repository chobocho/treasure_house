// main.rs — units 를 가져다 쓰는 크레이트
use units::{Foot, Meter, Unit};

// 조건으로 쓰는 것과 메서드를 부르는 것은 밖에서도 된다.
fn show<U: Unit>(unit: &U) {
    println!("{} 번 칸 {}", unit.index(), units::name(unit));
}

fn main() {
    show(&Meter);
    show(&Foot);
}
