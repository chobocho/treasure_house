use std::mem::transmute;

fn main() {
    let x: f32 = 1.0;
    // 써야 하는 길 — 안전한 메서드 한 쌍
    let bits: u32 = x.to_bits();
    println!("{bits:#010x} {}", f32::from_bits(bits));

    // 안전: f32 와 u32 는 크기가 같고, 32 비트의 어떤 값이든 u32 다.
    let raw: u32 = unsafe { transmute::<f32, u32>(x) };
    println!("{}", raw == bits);

    let n: u32 = 0x1234_5678;
    // 안전: [u8; 4] 와 u32 는 크기가 같고, 어떤 네 바이트든 [u8; 4] 다.
    let bytes: [u8; 4] = unsafe { transmute::<u32, [u8; 4]>(n) };
    // 바이트의 순서는 기계가 정한다. 그 순서로 주는 메서드와 견준다.
    println!("{}", bytes == n.to_ne_bytes());
    println!("{}", u32::from_ne_bytes(bytes) == n);
}
//@ warnings: show
