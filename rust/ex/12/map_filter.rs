fn main() {
    let scores = [72, 95, 58, 88];

    // map — 원소마다 바꾼다.
    let bonus: Vec<i32> = scores.iter().map(|s| s + 5).collect();
    // filter — 조건에 맞는 것만 남긴다.
    let passed: Vec<&i32> =
        scores.iter().filter(|s| **s >= 60).collect();
    // 이어 붙인다.
    let top: Vec<i32> = scores
        .iter()
        .filter(|s| **s >= 80)
        .map(|s| s * 10)
        .collect();

    println!("{bonus:?}\n{passed:?}\n{top:?}");
}
