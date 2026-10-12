// 파일에 그대로 쓸 머리 부분. 8 바이트라고 믿고 쓴 코드가 있다.
struct Header {
    kind: u8,
    flags: u8,
    checksum: u16,
    length: u32,
    // 나중에 칸 하나를 더했다.
    version: u8,
}

// 크기가 8 이 아니면 컴파일하지 않는다.
const _: () = assert!(size_of::<Header>() == 8);

fn main() {
    let h = Header {
        kind: 1,
        flags: 0,
        checksum: 7,
        length: 16,
        version: 2,
    };
    println!("{} {} {} {}", h.kind, h.flags, h.checksum, h.length);
    println!("{} {}", h.version, size_of::<Header>());
}
//@ expect: E0080
