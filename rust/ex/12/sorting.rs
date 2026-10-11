fn main() {
    let mut people =
        vec![("kim", 31), ("lee", 25), ("park", 31), ("choi", 19)];

    // 나이순 — 같은 나이는 원래 순서 그대로(안정 정렬)
    people.sort_by_key(|p| p.1);
    println!("{people:?}");

    // 나이는 내림차순, 같으면 이름 오름차순
    people.sort_by(|a, b| b.1.cmp(&a.1).then(a.0.cmp(b.0)));
    println!("{people:?}");

    let mut prices: Vec<f64> = vec![3.5, 1.25, 9.0];
    prices.sort_by(|a, b| a.total_cmp(b));
    println!("{prices:?}");
}
