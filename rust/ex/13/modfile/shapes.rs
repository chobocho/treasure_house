// shapes 의 하위 모듈 circle 은 shapes/circle.rs 에 있다.
pub mod circle;

pub fn area(w: u32, h: u32) -> u32 {
    w * h
}
