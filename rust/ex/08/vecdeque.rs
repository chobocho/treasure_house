use std::collections::VecDeque;

fn main() {
    // 양쪽 끝에서 넣고 뺄 수 있다 — 줄 서기(큐)에 쓴다.
    let mut queue = VecDeque::new();
    queue.push_back("첫째");
    queue.push_back("둘째");
    queue.push_front("새치기");
    println!("{queue:?}");

    println!("{:?}", queue.pop_front());
    println!("{:?}", queue.pop_back());
    println!("{queue:?} {:?}", queue.front());
}
