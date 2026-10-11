fn main() {
    let mut scores = vec![1, 2, 3];
    let first = &scores[0]; // 여기서 빌린다
    println!("first = {first}"); // 마지막으로 쓴다 — 빌림은 여기서 끝
    scores.push(4); // 그래서 이제 고쳐도 된다
    println!("{scores:?}");
}
