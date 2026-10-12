// units.rs — 라이브러리 크레이트
pub trait Unit {
    // NAMES 의 몇 번 칸인가
    fn index(&self) -> usize;
}

pub struct Meter;
pub struct Foot;

impl Unit for Meter {
    fn index(&self) -> usize {
        0
    }
}

impl Unit for Foot {
    fn index(&self) -> usize {
        1
    }
}

const NAMES: [&str; 2] = ["m", "ft"];

// Unit 은 Meter 와 Foot 뿐이라고 믿고 쓴 함수
pub fn name(unit: &dyn Unit) -> &'static str {
    NAMES[unit.index()]
}
