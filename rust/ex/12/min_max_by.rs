fn main() {
    let words = ["rust", "go", "python"];
    let prices: [f64; 3] = [3.5, 1.25, 9.0];

    println!("{:?}", words.iter().max_by_key(|w| w.len()));
    println!("{:?}", words.iter().min_by_key(|w| w.len()));
    // 실수에는 순서가 없어(NaN) max 를 못 쓴다 — 견주는 법을 준다.
    println!("{:?}", prices.iter().max_by(|a, b| a.total_cmp(b)));
}
