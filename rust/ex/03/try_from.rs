fn main() {
    let fits: i64 = 300;
    let big: i64 = 5_000_000_000;
    // 들어가면 Ok(값), 들어가지 않으면 Err(까닭)
    println!("{:?}", i32::try_from(fits));
    println!("{:?}", i32::try_from(big));
    println!("{:?}", u8::try_from(fits));
    println!("{:?}", u32::try_from(-1));
    // into 의 짝은 try_into 다
    let small: i32 = fits.try_into().expect("i32 에 안 들어간다");
    println!("small = {small}");
    // 실패했을 때 대신 쓸 값을 정해 둔다
    let level: u8 = fits.try_into().unwrap_or(u8::MAX);
    println!("level = {level}");
}
