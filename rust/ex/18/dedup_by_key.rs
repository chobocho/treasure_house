fn main() {
    // (이름, 시각) — 들어온 순서가 시각 순서다
    let mut log = vec![
        ("lee", 9),
        ("kim", 10),
        ("lee", 11),
        ("kim", 13),
        ("park", 14),
        ("lee", 15),
    ];
    // 이웃한 것만 지운다 — 지금은 같은 이름이 떨어져 있다
    let mut raw = log.clone();
    raw.dedup_by_key(|entry| entry.0);
    println!("{}", raw.len());

    // 이름으로 안정 정렬하면 같은 이름이 시각순으로 모인다
    log.sort_by_key(|entry| entry.0);
    println!("{log:?}");
    // 이름이 같은 이웃 가운데 첫 것만 남는다
    log.dedup_by_key(|entry| entry.0);
    println!("{log:?}");
}
