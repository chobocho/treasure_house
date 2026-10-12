fn double(x: i32) -> i32 {
    x * 2
}

// impl Fn 으로 받은 값을 받은 자리에서 잰다.
fn measure(f: impl Fn(i32) -> i32) -> usize {
    size_of_val(&f)
}

fn main() {
    let offset: i32 = 10;
    // 붙잡은 것이 없는 클로저와 i32 하나를 붙잡은 클로저
    let plain = |x: i32| x * 2;
    let shifted = move |x: i32| x + offset;
    // 함수 포인터
    let ptr: fn(i32) -> i32 = double;
    // 트레이트 객체 둘
    let by_ref: &dyn Fn(i32) -> i32 = &shifted;
    let boxed: Box<dyn Fn(i32) -> i32> = Box::new(move |x| x + offset);

    println!("{} {}", size_of_val(&plain), size_of_val(&shifted));
    println!("{} {}", size_of_val(&double), size_of_val(&ptr));
    println!("{} {}", size_of_val(&by_ref), size_of_val(&boxed));
    println!("{} {} {}", plain(1), shifted(1), double(1));
    println!("{} {} {}", ptr(1), by_ref(1), boxed(1));
    let inside = (measure(plain), measure(shifted), measure(ptr));
    println!("{inside:?}");
}
