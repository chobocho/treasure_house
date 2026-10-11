fn main() {
    let stock: i64 = 1000;
    let order: i32 = 3;
    // 넓은 타입으로: 값이 그대로다
    println!("{}", stock > order as i64);
    println!("-1_i8 as i32   = {}", -1_i8 as i32);
    println!("200_u8 as u32  = {}", 200_u8 as u32);
    // 좁은 타입으로: 들어가지 않는 윗비트를 잘라 낸다
    println!("300_i32 as u8  = {}", 300_i32 as u8);
    println!("-1_i32 as u8   = {}", -1_i32 as u8);
    // 크기는 같고 부호만 다르면: 비트는 그대로, 읽는 법이 바뀐다
    println!("-1_i32 as u32  = {}", -1_i32 as u32);
    println!("200_u8 as i8   = {}", 200_u8 as i8);
}
