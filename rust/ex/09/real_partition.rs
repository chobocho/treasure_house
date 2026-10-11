fn main() {
    let inputs = ["1", "둘", "3", "넷"];

    // 되는 것은 되는 대로, 안 되는 것은 따로 모은다.
    let mut numbers = Vec::new();
    let mut failed = Vec::new();
    for s in inputs {
        match s.parse::<i32>() {
            Ok(n) => numbers.push(n),
            Err(_) => failed.push(s),
        }
    }
    println!("{numbers:?} / 실패: {failed:?}");

    // 실패는 조용히 버리고 싶다면 한 줄로.
    let only: Vec<i32> =
        inputs.iter().filter_map(|s| s.parse().ok()).collect();
    println!("{only:?}");
}
