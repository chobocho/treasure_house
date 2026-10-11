fn stars(n: u32) -> String {
    let mut s = String::new();
    for _ in 0..n {
        s.push('*');
    }
    // 지역 변수지만 정리되지 않는다. 주인이 부른 쪽으로 바뀐다.
    s
}

fn main() {
    let line = stars(5);
    println!("{line}");
}
