trait Unit {
    // 연관 상수 — 타입마다 다른 값을 갖는 상수.
    const SYMBOL: &'static str;
    const PER_BASE: f64;

    fn show(value: f64) -> String {
        format!("{} {}", value * Self::PER_BASE, Self::SYMBOL)
    }
}

struct Meter;
struct Centimeter;

impl Unit for Meter {
    const SYMBOL: &'static str = "m";
    const PER_BASE: f64 = 1.0;
}

impl Unit for Centimeter {
    const SYMBOL: &'static str = "cm";
    const PER_BASE: f64 = 100.0;
}

fn main() {
    println!("{} / {}", Meter::show(1.5), Centimeter::show(1.5));
    // 표준 라이브러리의 연관 상수
    println!("{} {}", i32::MAX, u8::BITS);
}
