use std::ffi::c_int;

extern "C" {
    fn abs(n: c_int) -> c_int;
}

fn main() {
    // 안전: -7 의 절댓값 7 은 c_int 에 들어간다.
    let n = unsafe { abs(-7) };
    println!("{n}");
}
//@ edition: 2021
