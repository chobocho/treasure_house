// 같은 네 바이트를 수 하나로도, 바이트 넷으로도 본다.
#[repr(C)]
union Bits {
    n: u32,
    bytes: [u8; 4],
}

fn main() {
    // 필드 하나만 골라 만든다.
    let b = Bits { n: 0x1234_5678 };
    println!("{}", size_of::<Bits>());

    // 안전: 마지막으로 넣은 필드가 n 이다.
    let n = b.n;
    println!("{n:#x}");

    // 안전: 네 바이트가 모두 채워져 있고, [u8; 4] 에는 안 되는 비트
    // 모양이 없다.
    let bytes = unsafe { b.bytes };
    println!("{}", bytes == n.to_ne_bytes());
}
//@ expect: E0133
