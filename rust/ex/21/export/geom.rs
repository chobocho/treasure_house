// 라이브러리 크레이트 geom
pub mod shapes {
    // 모듈 안에 적은 매크로를 크레이트 밖으로 내놓는다.
    #[macro_export]
    macro_rules! square {
        ($side:expr) => {{
            let s = $side;
            s * s
        }};
    }
}
