use std::ffi::c_int;

// C 의 div_t 와 같은 모양. 이 기계의 stdlib.h 에는 int 둘이 quot,
// rem 순서로 적혀 있다.
struct DivT {
    quot: c_int,
    rem: c_int,
}

unsafe extern "C" {
    // 몫과 나머지를 구조체 하나에 담아 값으로 돌려준다.
    unsafe fn div(numer: c_int, denom: c_int) -> DivT;
}

fn main() {
    // 안전: 나누는 수가 0 이 아니고, 몫 3 과 -3 은 c_int 에 들어간다.
    let (a, b) = unsafe { (div(17, 5), div(-17, 5)) };
    println!("{} {}", a.quot, a.rem);
    println!("{} {}", b.quot, b.rem);
    println!("{} {}", -17 / 5, -17 % 5);
    println!("{}", size_of::<DivT>() == 2 * size_of::<c_int>());
}
//@ warnings: show
//@ norun
