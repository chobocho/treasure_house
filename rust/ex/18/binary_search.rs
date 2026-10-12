fn main() {
    let mut ids = vec![12, 25, 31, 47, 58];
    println!("{}", ids.is_sorted());
    // 있으면 Ok(그 자리), 없으면 Err(끼워 넣을 자리)
    println!("{:?}", ids.binary_search(&31));
    println!("{:?}", ids.binary_search(&40));
    println!(
        "{:?} {:?}",
        ids.binary_search(&5),
        ids.binary_search(&99)
    );
    // Err 가 알려 준 자리에 넣으면 정렬된 채로 남는다
    if let Err(at) = ids.binary_search(&40) {
        ids.insert(at, 40);
    }
    println!("{ids:?} {}", ids.is_sorted());

    // 정렬돼 있지 않은 벡터에 같은 것을 묻는다
    let mixed = vec![58, 12, 47, 31, 25];
    println!("{}", mixed.is_sorted());
    println!("{:?}", mixed.binary_search(&31));
    println!("{}", mixed.contains(&31));
}
