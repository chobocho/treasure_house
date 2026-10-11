fn main() {
    // 끝이 없는 범위도 반복자다 — 게으르므로 필요한 만큼만 돈다.
    let squares: Vec<u64> = (1u64..)
        .map(|n| n * n)
        .filter(|n| n % 3 == 1)
        .take(5)
        .collect();
    println!("{squares:?}");
}
