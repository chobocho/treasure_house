static mut CALLS: u32 = 0;

fn main() {
    // 안전: 스레드가 하나뿐이고, 고치는 동안 살아 있는 참조가 없다.
    unsafe { CALLS += 1 };

    // 안전: 스레드가 하나뿐이고, r 이 사는 동안 CALLS 를 고치지 않는다.
    let r = unsafe { &CALLS };
    println!("{r}");

    // 안전: 위와 같다.
    unsafe { println!("{}", CALLS) };
}
//@ expect: error
