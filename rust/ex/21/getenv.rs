use std::env;
use std::ffi::{CStr, c_char};

unsafe extern "C" {
    // 없는 이름이면 널을, 있으면 그 값을 가리키는 포인터를 준다.
    unsafe fn getenv(name: *const c_char) -> *const c_char;
}

// C 의 getenv 로 환경 변수를 읽어, String 으로 복사해 돌려준다.
fn c_getenv(name: &CStr) -> Option<String> {
    // 안전: name 은 0 으로 끝난다. 이 프로그램은 스레드가 하나라서
    // 읽는 동안 환경을 고치는 쪽이 없다.
    let p = unsafe { getenv(name.as_ptr()) };
    if p.is_null() {
        return None;
    }
    // 안전: 널이 아닌 p 는 0 으로 끝나는 글을 가리킨다. 환경을 다시
    // 고치기 전에, 빌린 글을 여기서 바로 복사해 둔다.
    let text: &CStr = unsafe { CStr::from_ptr(p) };
    println!("  빌린 글 {:?} {:?}", text, text.to_str());
    text.to_str().ok().map(|s| s.to_string())
}

fn main() {
    // 안전: 스레드가 하나뿐일 때 환경을 고친다.
    unsafe {
        env::set_var("DECK_LANG", "rust");
        env::remove_var("DECK_NO_SUCH_NAME");
    }
    println!("{:?}", c_getenv(c"DECK_LANG"));
    println!("{:?}", c_getenv(c"DECK_NO_SUCH_NAME"));
}
