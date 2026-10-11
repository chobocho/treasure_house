fn main() {
    // b"…" — 바이트 문자열. 타입은 &[u8; N] 이다.
    let bytes = b"hi!";
    println!("{bytes:?} {}", bytes.len());

    // String ↔ 바이트.
    let s = String::from("가");
    println!("{:?}", s.as_bytes());
    println!("{:?}", String::from_utf8(vec![0xea, 0xb0, 0x80]));
    // 0xff 는 올바른 UTF-8 이 아니다 — Err 가 나온다.
    println!("{}", String::from_utf8(vec![0xff]).is_err());
}
