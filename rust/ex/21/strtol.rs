use std::ffi::{CStr, c_char, c_int, c_long};
use std::ptr;

unsafe extern "C" {
    // s 의 앞에서 수를 읽어 돌려주고, 읽다 멈춘 자리를 *end 에 적는다.
    unsafe fn strtol(
        s: *const c_char,
        end: *mut *mut c_char,
        base: c_int,
    ) -> c_long;
}

// 글의 앞에서 읽은 수와, 읽은 바이트 수를 돌려준다.
fn leading_number(text: &CStr) -> (c_long, isize) {
    let mut end: *mut c_char = ptr::null_mut();
    // 안전: text 는 0 으로 끝난다. end 는 살아 있는 변수이고, strtol 은
    // 거기에 포인터 하나를 적는다. 예제의 수는 c_long 에 들어간다.
    let n = unsafe { strtol(text.as_ptr(), &raw mut end, 10) };
    // 안전: strtol 이 적어 준 end 는 text 의 글 안이나 끝의 0 을
    // 가리킨다. 같은 자리 안의 두 포인터다.
    let end = end as *const c_char;
    let used = unsafe { end.offset_from(text.as_ptr()) };
    (n, used)
}

fn main() {
    println!("{:?}", leading_number(c"120km"));
    println!("{:?}", leading_number(c"-7"));
    println!("{:?}", leading_number(c"km"));
}
