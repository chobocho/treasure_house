use std::mem::offset_of;

// 필드의 크기를 더하면 1 + 4 + 1 = 6 바이트다
#[allow(dead_code)]
struct Plain {
    a: u8,
    b: u32,
    c: u8,
}

// 같은 필드를 적은 순서대로 놓게 한다
#[allow(dead_code)]
#[repr(C)]
struct Fixed {
    a: u8,
    b: u32,
    c: u8,
}

fn main() {
    // 크기와 정렬
    println!("u8    {} {}", size_of::<u8>(), align_of::<u8>());
    println!("u32   {} {}", size_of::<u32>(), align_of::<u32>());
    println!("Plain {} {}", size_of::<Plain>(), align_of::<Plain>());
    println!("Fixed {} {}", size_of::<Fixed>(), align_of::<Fixed>());

    // 필드가 놓인 자리 — 구조체의 맨 앞에서 몇 바이트째인가
    println!("Fixed a {}", offset_of!(Fixed, a));
    println!("Fixed b {}", offset_of!(Fixed, b));
    println!("Fixed c {}", offset_of!(Fixed, c));
    println!("Plain a {}", offset_of!(Plain, a));
    println!("Plain b {}", offset_of!(Plain, b));
    println!("Plain c {}", offset_of!(Plain, c));

    // 값으로 묻는다 — u16 다섯 칸짜리 배열
    println!("{}", size_of_val(&[0_u16; 5]));
}
