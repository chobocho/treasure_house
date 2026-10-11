use std::cmp::Reverse;
use std::collections::BinaryHeap;

fn main() {
    // 늘 가장 큰 것이 먼저 나온다 — 우선순위 큐.
    let mut heap = BinaryHeap::from([3, 9, 4]);
    heap.push(7);
    println!("{:?}", heap.peek()); // 꺼내지 않고 본다
    while let Some(top) = heap.pop() {
        print!("{top} ");
    }
    println!();

    // 가장 작은 것부터 꺼내려면 Reverse 로 감싼다.
    let mut min_heap =
        BinaryHeap::from([Reverse(3), Reverse(9), Reverse(4)]);
    if let Some(Reverse(n)) = min_heap.pop() {
        println!("{n}"); // 꺼내면서 포장을 벗긴다
    }
}
