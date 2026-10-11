fn main() {
    let scores = [90, 85, 70];
    // 다른 언어의 습관 — 번호로 돌며 꺼낸다. 되기는 한다.
    for i in 0..scores.len() {
        println!("{}", scores[i]);
    }
    // Rust 다운 방식 — 원소를 직접 받는다.
    for s in scores {
        println!("{s}");
    }
}
