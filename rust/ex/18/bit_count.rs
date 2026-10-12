fn main() {
    // 오른쪽 끝(0번)이 월요일 — 수 목 토에 나왔다
    let days: u8 = 0b0010_1100;
    println!("{days:08b}");
    // 켜진 비트의 수가 나온 날의 수다
    println!("나온 날 수      {}", days.count_ones());
    // 오른쪽에 이어진 0 의 수가 처음 나온 날의 번호다
    println!("처음 나온 날    {}번", days.trailing_zeros());
    // 왼쪽에 이어진 0 의 수로 마지막 날의 번호를 얻는다
    let last = u8::BITS - 1 - days.leading_zeros();
    println!("마지막 나온 날  {last}번");
    // 비트가 꼭 하나만 켜져 있는가
    println!("하루만 나왔는가 {}", days.is_power_of_two());
    println!("0b0010_0000 은  {}", 0b0010_0000_u8.is_power_of_two());
    // 켜진 비트가 없으면 0 의 수가 비트 수와 같다
    println!("0 의 뒤쪽 0     {}", 0_u8.trailing_zeros());
}
