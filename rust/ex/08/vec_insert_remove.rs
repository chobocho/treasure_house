fn main() {
    let mut v = vec!['a', 'b', 'c', 'd'];

    v.insert(1, 'X'); // 뒤의 것들을 한 칸씩 민다
    println!("{v:?}");
    let gone = v.remove(1); // 뒤의 것들을 한 칸씩 당긴다
    println!("{v:?} (뺀 것 {gone})");
    let fast = v.swap_remove(0); // 마지막 것으로 메운다 — 순서는 깨진다
    println!("{v:?} (뺀 것 {fast})");
    v.truncate(2); // 앞의 둘만 남긴다
    println!("{v:?}");
}
