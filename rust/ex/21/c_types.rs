use std::any::type_name;
use std::ffi::{c_char, c_int, c_long, c_void};

fn main() {
    // C 의 int 와 long 에 맞춘 이름. 이 기계에서 무엇의 별명인지 본다.
    println!("{} {}", type_name::<c_int>(), size_of::<c_int>());
    println!("{} {}", type_name::<c_long>(), size_of::<c_long>());
    // C 의 char 는 한 바이트다. 부호가 있는지는 대상 플랫폼마다
    // 달라서 찍지 않는다.
    println!("{}", size_of::<c_char>());
    // void* 는 무엇을 가리키는지 적지 않은 포인터다.
    println!("{}", size_of::<*const c_void>() == size_of::<usize>());
}
