use std::ffi::c_int;

// Rust 쪽에서 경로로 부르는 평범한 함수
pub fn add(a: i32, b: i32) -> i32 {
    a.wrapping_add(b)
}

// C 쪽에 내놓는 함수. 기호 이름이 글자 그대로 calc_add 가 된다.
#[unsafe(no_mangle)]
pub extern "C" fn calc_add(a: c_int, b: c_int) -> c_int {
    add(a, b)
}

// 기호 이름을 함수 이름과 다르게 정한다.
#[unsafe(export_name = "calc_twice")]
pub extern "C" fn double(n: c_int) -> c_int {
    add(n, n)
}
