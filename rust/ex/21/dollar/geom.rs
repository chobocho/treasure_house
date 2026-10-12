// 라이브러리 크레이트 geom
pub fn area(w: u32, h: u32) -> u32 {
    w * h
}

// 본문이 같은 크레이트의 함수 area 를 부른다.
#[macro_export]
macro_rules! square_area {
    ($side:expr) => {
        area($side, $side)
    };
}
