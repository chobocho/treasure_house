fn main() {
    let s1 = String::from("hello");
    // 힙의 글자까지 새로 만든다
    let mut s2 = s1.clone();

    // 한쪽을 고쳐도 다른 쪽은 그대로다
    s2.push_str(", world");
    println!("s1 = {s1}");
    println!("s2 = {s2}");
}
