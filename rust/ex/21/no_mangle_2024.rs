use std::ffi::c_int;

#[no_mangle]
pub extern "C" fn calc_add(a: c_int, b: c_int) -> c_int {
    a.wrapping_add(b)
}

fn main() {
    println!("{}", calc_add(2, 3));
}
//@ expect: error
