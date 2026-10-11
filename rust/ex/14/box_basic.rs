fn main() {
    let on_stack = 5;
    let on_heap = Box::new(5); // 값 5 는 힙에, b 에는 그 주소가 든다

    println!("{} {}", on_stack, on_heap);
    println!("{}", *on_heap + 1); // * 로 속의 값을 꺼낸다
    // Box 자체는 포인터 하나의 크기다
    println!("{}", std::mem::size_of_val(&on_heap));
} // on_heap 이 범위를 벗어나면 힙의 5 도 함께 정리된다
