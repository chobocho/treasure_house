fn main() {
    let level: u8 = 250;
    // checked — 넘치면 None, 아니면 Some(값)
    println!("checked     {:?}", level.checked_add(10));
    println!("checked     {:?}", level.checked_add(5));
    // wrapping — 넘치면 0 부터 다시 센다
    println!("wrapping    {}", level.wrapping_add(10));
    // saturating — 넘치면 끝값에 멈춘다
    println!("saturating  {}", level.saturating_add(10));
    // overflowing — 돌아간 값과 넘쳤는지를 함께 준다
    println!("overflowing {:?}", level.overflowing_add(10));
}
