use std::ffi::{CString, c_char};

unsafe extern "C" {
    unsafe fn strlen(s: *const c_char) -> usize;
}

fn main() {
    // 변수에 담지 않은 CString 은 이 문이 끝날 때 정리된다.
    let p = CString::new("hello").unwrap().as_ptr();
    // 그래서 여기서 p 는 이미 돌려준 자리를 가리킨다.
    let n = unsafe { strlen(p) };
    println!("{n}");
}
//@ warnings: show
//@ norun
