use std::ffi::{CStr, c_char, c_int};

// C 표준 라이브러리의 함수를 빌려 쓴다.
unsafe extern "C" {
    fn abs(n: c_int) -> c_int;
    fn strlen(s: *const c_char) -> usize;
}

fn main() {
    let text: &CStr = c"hello"; // 끝에 0 이 붙는 C 문자열
    // 안전: abs 는 어떤 정수든 받고, text 는 0 으로 끝난다.
    let (a, n) = unsafe { (abs(-7), strlen(text.as_ptr())) };
    println!("{a} {n}");
}
