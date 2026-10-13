// 걸은 거리 — 미터로 적어 둔다.
const WALKED_M: f64 = 4200.0;

// metric 이 켜져 있으면 km 로, 꺼져 있으면 mile 로 바꾼다.
#[cfg(feature = "metric")]
fn convert(meters: f64) -> (f64, &'static str) {
    (meters / 1000.0, "km")
}

#[cfg(not(feature = "metric"))]
fn convert(meters: f64) -> (f64, &'static str) {
    (meters / 1609.344, "mile")
}

fn main() {
    let (value, unit) = convert(WALKED_M);
    // precise 는 소수 자릿수만 고른다.
    if cfg!(feature = "precise") {
        println!("{value:.3} {unit}");
    } else {
        println!("{value:.1} {unit}");
    }
}
