fn main() {
    let mut s = String::with_capacity(16); // 자리를 미리 잡는다
    println!("{} {}", s.len(), s.capacity());
    for _ in 0..4 {
        s.push_str("ab");
    }
    println!("{} {}", s.len(), s.capacity()); // 다시 잡지 않았다
    s.clear();
    println!("{} {}", s.len(), s.capacity()); // 내용만 비운다
}
