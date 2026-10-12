fn main() {
    // (이름, 반) — 접수한 순서대로 적혀 있다
    let arrived = vec![
        ("yoon", 2),
        ("kim", 1),
        ("choi", 2),
        ("park", 1),
        ("lee", 2),
    ];

    // sort_by_key 는 안정 정렬 — 반이 같으면 접수한 순서 그대로
    let mut stable = arrived.clone();
    stable.sort_by_key(|&(_, class)| class);
    println!("{stable:?}");

    // sort_unstable_by_key — 반의 순서만 찍어 본다
    let mut unstable = arrived.clone();
    unstable.sort_unstable_by_key(|&(_, class)| class);
    let classes: Vec<u32> = unstable.iter().map(|&(_, c)| c).collect();
    println!("{classes:?}");

    // 원소를 통째로 견주면 같은 것끼리는 구별할 수 없다
    let mut a = vec![3, 1, 2, 1, 3];
    let mut b = a.clone();
    a.sort();
    b.sort_unstable();
    println!("{a:?} {}", a == b);
}
