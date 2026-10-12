use std::ptr::{self, NonNull};

fn main() {
    let mut n = 5_i32;
    // new 는 널이 아닐 때만 Some 을 준다.
    let some = NonNull::new(&raw mut n);
    let none = NonNull::new(ptr::null_mut::<i32>());
    println!("{} {}", some.is_some(), none.is_none());

    // Option 으로 감싸도 날 포인터 하나와 크기가 같다.
    let a = size_of::<Option<NonNull<i32>>>();
    let b = size_of::<*mut i32>();
    println!("{}", a == b);

    if let Some(p) = some {
        // 안전: p 는 살아 있는 n 을 가리키고 정렬이 맞다. 이 블록이
        // 끝날 때까지 n 을 다른 길로 읽거나 고치지 않는다.
        unsafe {
            *p.as_ptr() += 1;
            println!("{}", *p.as_ref());
        }
    }
    println!("{n}");
}
