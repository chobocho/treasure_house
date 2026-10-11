fn main() {
    let mut v = Vec::new();
    let mut last = v.capacity();
    println!("길이 0, 자리 {last}");
    for n in 1..=20 {
        v.push(n);
        if v.capacity() != last {
            // 자리가 모자라면 더 큰 곳으로 옮겨 간다.
            last = v.capacity();
            println!("길이 {n}, 자리 {last}");
        }
    }
}
