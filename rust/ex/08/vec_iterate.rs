fn main() {
    let mut prices = vec![100, 250, 80];

    for p in &prices {
        print!("{p} "); // 읽기
    }
    println!();
    for p in &mut prices {
        *p += 10; // 고치기 — * 로 따라가서 쓴다
    }
    println!("{prices:?}");
    for (i, p) in prices.iter().enumerate() {
        print!("{i}:{p} ");
    }
    println!();
}
