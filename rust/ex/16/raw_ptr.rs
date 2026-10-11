fn main() {
    let mut n = 5;
    // 날 포인터를 만드는 것은 안전하다.
    let reader = &raw const n;
    let writer = &raw mut n;

    // 따라가는 것은 unsafe — "유효한 주소임을 내가 보증한다".
    unsafe {
        *writer += 1;
        println!("{}", *reader);
    }
}
