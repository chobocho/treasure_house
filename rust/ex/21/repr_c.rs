use std::mem::offset_of;

// 적은 순서대로 놓는다. 필드마다 자기 정렬의 배수인 자리에 온다.
#[repr(C)]
#[allow(dead_code)]
struct Wide {
    tag: u8,
    value: u32,
    flag: u8,
    count: u16,
}

// 같은 필드 넷을 큰 것부터 적었다.
#[repr(C)]
#[allow(dead_code)]
struct Tight {
    value: u32,
    count: u16,
    tag: u8,
    flag: u8,
}

// 타입 이름과 필드마다 놓인 자리, 빗금 뒤에 전체 크기와 정렬을 찍는다.
macro_rules! layout {
    ($ty:ident: $($field:ident)+) => {
        print!("{}", stringify!($ty));
        $( print!(" {}", offset_of!($ty, $field)); )+
        println!(" / {} {}", size_of::<$ty>(), align_of::<$ty>());
    };
}

fn main() {
    let aligns =
        [align_of::<u8>(), align_of::<u16>(), align_of::<u32>()];
    println!("{aligns:?}");
    layout!(Wide: tag value flag count);
    layout!(Tight: value count tag flag);
}
