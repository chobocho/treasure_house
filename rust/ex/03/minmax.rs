fn main() {
    // 타입마다 가장 작은 값과 가장 큰 값이 이름으로 들어 있다
    println!("i8   {} ~ {}", i8::MIN, i8::MAX);
    println!("u8   {} ~ {}", u8::MIN, u8::MAX);
    println!("i32  {} ~ {}", i32::MIN, i32::MAX);
    println!("u32  {} ~ {}", u32::MIN, u32::MAX);
    println!("i64  {} ~ {}", i64::MIN, i64::MAX);
    println!("u64  {} ~ {}", u64::MIN, u64::MAX);
    println!("u128 {} ~ {}", u128::MIN, u128::MAX);
    // BITS 는 그 타입이 차지하는 비트 수
    println!("i8 {}비트, i32 {}비트", i8::BITS, i32::BITS);
    println!("isize {}비트, usize {}비트", isize::BITS, usize::BITS);
}
