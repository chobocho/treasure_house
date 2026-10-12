use std::ffi::c_int;

// 부르는 쪽이 아는 것은 이름과 타입뿐이다. C 라면 헤더에 적을 선언이다.
unsafe extern "C" {
    safe fn calc_add(a: c_int, b: c_int) -> c_int;
    safe fn calc_twice(n: c_int) -> c_int;
}

fn main() {
    // 경로로 부른다.
    println!("{}", calc::add(2, 3));
    // 기호 이름으로 부른다.
    println!("{}", calc_add(2, 3));
    println!("{}", calc_twice(21));
}
