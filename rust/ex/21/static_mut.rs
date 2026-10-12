// 바뀔 수 있는 전역 변수. 읽는 것도 고치는 것도 unsafe 다.
static mut CALLS: u32 = 0;

fn record() {
    // 안전: 이 프로그램은 스레드가 하나뿐이고, CALLS 를 가리키는 참조를
    // 어디에도 만들지 않는다.
    unsafe { CALLS += 1 };
}

fn main() {
    record();
    record();
    // 안전: 위와 같다. 값을 복사해 읽는다.
    let n = unsafe { CALLS };
    println!("{n}");
}
