fn main() {
    // char → 수: 유니코드 번호가 나온다
    println!("'A' as u32  = {}", 'A' as u32);
    println!("'A' as u8   = {}", 'A' as u8);
    println!("'각' as u32 = {:#x}", '각' as u32);
    // u8 → char: 그 번호의 글자가 된다
    println!("97_u8 as char = {}", 97_u8 as char);
    // 글자로 셈하기 — 'a' 에서 세 칸 뒤
    println!("{}", (b'a' + 3) as char);
    // u32 → char 는 함수로 — 글자가 아닌 번호도 있기 때문이다
    println!("{:?}", char::from_u32(0xAC01));
    println!("{:?}", char::from_u32(0xD800));
    // bool → 수
    println!("{} {}", true as u8, false as u8);
}
