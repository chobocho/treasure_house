use std::cmp::Reverse;

fn main() {
    let mut scores =
        vec![("park", 85), ("kim", 92), ("lee", 85), ("choi", 70)];
    // 점수 내림차순 — 키를 Reverse 로 감싼다
    scores.sort_by_key(|&(_, score)| Reverse(score));
    println!("{scores:?}");
    // 점수는 내림차순, 같으면 이름 오름차순 — 튜플 키
    scores.sort_by_key(|&(name, score)| (Reverse(score), name));
    println!("{scores:?}");

    // Reverse 끼리 견주면 속에 든 값의 순서가 뒤집힌다
    println!("{} {}", 1 < 2, Reverse(1) < Reverse(2));
    // 꺼낼 때는 .0
    let best = scores.iter().map(|&(_, s)| Reverse(s)).min();
    println!("{:?} {:?}", best, best.map(|r| r.0));
}
