// 거리를 f64 로만 다룬다. 단위는 변수 이름에만 적혀 있다.
fn total(a: f64, b: f64) -> f64 {
    a + b
}

fn main() {
    let runway_m = 1200.0;
    let taxi_ft = 300.0;
    // 미터와 피트를 그대로 더했다.
    println!("{}", total(runway_m, taxi_ft));
}
