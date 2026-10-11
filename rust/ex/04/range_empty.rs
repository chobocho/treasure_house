fn main() {
    // 거꾸로 된 범위는 비어 있다 — 한 번도 돌지 않는다.
    for i in 5..1 {
        println!("{i}");
    }
    println!("끝");
    println!("{} {}", (5..1).len(), (1..5).len());
}
