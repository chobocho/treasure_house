use std::ffi::{c_char, c_int};

// C 표준 라이브러리의 함수 셋. 선언마다 safe 나 unsafe 를 적을 수 있다.
unsafe extern "C" {
    // 어떤 f64 를 넣어도 된다.
    safe fn sqrt(x: f64) -> f64;
    // 0 으로 끝나는 글을 가리키는 포인터만 넣어야 한다.
    unsafe fn strlen(s: *const c_char) -> usize;
    // 아무것도 적지 않으면 unsafe 다.
    fn atoi(s: *const c_char) -> c_int;
}

fn main() {
    // safe 로 선언한 함수는 unsafe 블록 없이 부른다.
    println!("{}", sqrt(16.0));

    // 안전: 리터럴 c"hello" 는 0 으로 끝난다.
    let len = unsafe { strlen(c"hello".as_ptr()) };
    // 안전: 리터럴 c"42" 는 0 으로 끝나고, 42 는 c_int 에 들어간다.
    let n = unsafe { atoi(c"42".as_ptr()) };
    println!("{len} {n}");
}
