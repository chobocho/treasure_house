use std::cmp;

fn main() {
    // 값 둘 가운데 고른다 — 메서드로도, 함수로도
    println!("{} {}", 3.min(8), 3.max(8));
    println!("{} {}", cmp::min(3, 8), cmp::max(3, 8));
    // 수가 아니어도 순서가 있는 값이면 된다
    println!("{} {:?}", "pear".min("apple"), (1, 'b').max((1, 'a')));

    // 음량을 0 과 100 사이에 가둔다
    for volume in [-5, 40, 130] {
        println!("{volume:>4} → {}", volume.clamp(0, 100));
    }
    // 손으로 적으면 아래 끝에 max, 위 끝에 min 이 온다
    println!("{}", 130.max(0).min(100));
    // 글에도 쓴다 — 등급을 B 와 D 사이로
    println!("{} {}", 'A'.clamp('B', 'D'), 'F'.clamp('B', 'D'));
}
