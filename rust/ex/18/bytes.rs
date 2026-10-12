fn main() {
    let n: u32 = 0x1234_5678;
    // be 는 큰 자리 바이트부터, le 는 작은 자리 바이트부터
    let be = n.to_be_bytes();
    let le = n.to_le_bytes();
    println!("be {be:02x?}");
    println!("le {le:02x?}");
    // 쓴 순서대로 읽으면 같은 수로 돌아온다
    println!("{:#x}", u32::from_be_bytes(be));
    println!("{:#x}", u32::from_le_bytes(le));
    // 순서를 바꿔 읽으면 다른 수가 된다
    println!("{:#x}", u32::from_le_bytes(be));

    // 읽어 온 바이트의 앞 네 칸을 길이로 읽는다
    let data: Vec<u8> = vec![0, 0, 1, 2, b'o', b'k'];
    let head: [u8; 4] = data[..4].try_into().unwrap();
    println!("{}", u32::from_be_bytes(head));
}
