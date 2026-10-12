fn main() {
    // 색상 코드 — 16 진수 여섯 자리
    let color = u32::from_str_radix("ff8800", 16).unwrap();
    println!("{color} = {color:#08x}");
    // 밀고 가려서 두 자리씩 꺼낸다
    let r = (color >> 16) & 0xff;
    let g = (color >> 8) & 0xff;
    let b = color & 0xff;
    println!("빨강 {r} 초록 {g} 파랑 {b}");

    // 2 진수와 36 진수도 같은 함수로 읽는다
    println!("{:?}", u8::from_str_radix("1010", 2));
    println!("{:?}", u32::from_str_radix("rust", 36));
    // 그 진법에 없는 숫자, 타입에 넘치는 값은 Err
    println!("{:?}", u8::from_str_radix("12", 2));
    println!("{:?}", u8::from_str_radix("100", 16));
    // 접두어 0x 도 읽지 못한다
    println!("{:?}", u32::from_str_radix("0xff", 16));
    // parse 는 10 진수로만 읽는다
    println!("{:?}", "ff".parse::<u32>());
}
