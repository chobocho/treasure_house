mod shapes {
    pub mod circle {
        pub fn area(r: f64) -> f64 {
            3.14 * r * r
        }
    }
    pub fn square(side: f64) -> f64 {
        side * side
    }
}

// use — 긴 경로를 이 스코프로 끌어온다.
use shapes::circle;
use shapes::square;

fn main() {
    println!("{}", shapes::circle::area(1.0)); // 전체 경로
    println!("{}", circle::area(1.0)); // 모듈까지만 끌어온 경우
    println!("{}", square(2.0)); // 함수를 직접 끌어온 경우
}
