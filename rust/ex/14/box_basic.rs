fn main() {
    let on_stack = 5;
    // 값 5 는 힙에 놓이고, 변수에는 그 주소가 든다.
    let mut on_heap = Box::new(5);

    println!("{} {}", on_stack, on_heap);
    *on_heap += 1; // * 로 속의 값에 닿는다 — 고치려면 mut
    println!("{}", on_heap);
    // Box 자체는 포인터 하나의 크기다 — 속이 1000 바이트여도.
    println!("{}", std::mem::size_of_val(&on_heap));
    println!("{}", std::mem::size_of::<Box<[u8; 1000]>>());
}
