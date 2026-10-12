use std::ffi::{CString, c_char};

unsafe extern "C" {
    unsafe fn strlen(s: *const c_char) -> usize;
}

fn main() {
    // 실행 중에 만든 글. 끝에 0 바이트가 없다.
    let name = format!("{}-{}", "rust", 2024);
    println!("{}", name.len());

    // CString::new 가 바이트를 넘겨받아 끝에 0 을 붙인다.
    let owned = CString::new(name).unwrap();
    println!("{:?} {}", owned, owned.as_bytes_with_nul().len());

    // 안전: owned 는 0 으로 끝나고, 이 호출이 끝난 뒤까지 살아 있다.
    let n = unsafe { strlen(owned.as_ptr()) };
    println!("{n}");

    // 가운데에 0 이 있는 글은 받지 않는다.
    let bad = CString::new("ab\0cd");
    println!("{bad:?}");
}
