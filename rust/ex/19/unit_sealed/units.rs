// units.rs — 라이브러리 크레이트
// 이 모듈에는 pub 이 없어서 크레이트 밖에서는 들어올 수 없다.
mod sealed {
    pub trait Sealed {}
}

// Unit 을 구현하려면 Sealed 부터 구현해야 한다.
pub trait Unit: sealed::Sealed {
    fn index(&self) -> usize;
}

pub struct Meter;
pub struct Foot;

impl sealed::Sealed for Meter {}
impl sealed::Sealed for Foot {}

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

pub fn name(unit: &dyn Unit) -> &'static str {
    NAMES[unit.index()]
}
