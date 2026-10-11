fn main() {
    let mut n = 5;
    // 날 포인터를 만드는 것은 안전하다.
    let writer = &raw mut n;
    // 같은 곳을 가리키는 읽기 전용 포인터. 참조라면 함께 둘 수 없다.
    let reader = writer as *const i32;

    // 따라가는 것은 unsafe — "유효한 주소임을 내가 보증한다".
    unsafe {
        *writer += 1;
        println!("{}", *reader);
    }
}
