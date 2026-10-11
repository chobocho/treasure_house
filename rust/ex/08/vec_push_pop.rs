fn main() {
    let mut stack = Vec::new(); // 타입은 아래의 push 를 보고 정해진다
    stack.push("a");
    stack.push("b");
    stack.push("c");
    println!("{stack:?} 길이 {}", stack.len());

    println!("{:?}", stack.pop()); // 끝에서 꺼낸다 — Option
    println!("{:?}", stack.pop());
    println!("{stack:?} 비었나 {}", stack.is_empty());
    stack.clear();
    println!("{:?}", stack.pop()); // 비었으면 None
}
