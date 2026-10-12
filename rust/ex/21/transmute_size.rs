use std::mem::transmute;

fn main() {
    let n: u32 = 0x1234_5678;
    // u32 는 네 바이트인데 받는 쪽은 세 바이트다.
    let bytes: [u8; 3] = unsafe { transmute::<u32, [u8; 3]>(n) };
    println!("{bytes:?}");
}
//@ expect: E0512
