fn main() {
    let mut temps = [21.5, f64::NAN, 19.0, 23.2];
    // total_cmp 는 NaN 까지 넣어 줄을 세우는 순서다
    temps.sort_by(f64::total_cmp);
    println!("{temps:?}");

    // max 와 min 은 NaN 을 건너뛴다
    let nan = f64::NAN;
    println!("21.5 와 NaN 중 큰 쪽  {}", 21.5_f64.max(nan));
    println!("21.5 와 NaN 중 작은 쪽 {}", 21.5_f64.min(nan));
}
