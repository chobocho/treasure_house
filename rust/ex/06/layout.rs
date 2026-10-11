fn main() {
    let mut s = String::from("hello");
    // size_of_val 은 스택에 놓인 부분의 크기만 센다
    println!("스택 {}바이트", size_of_val(&s));
    println!("len {} capacity {}", s.len(), s.capacity());

    // 글자가 늘면 힙 쪽이 자란다. 스택 쪽은 그대로다.
    s.push_str("!!");
    println!("스택 {}바이트", size_of_val(&s));
    println!("len {} capacity {}", s.len(), s.capacity());
}
