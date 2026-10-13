fn main() {
    let orange = (255_u8, 136_u8, 0_u8);
    let (r, g, b) = orange;
    // 곱한 값은 u8 에 들어가지 않으므로 먼저 u32 로 넓힌다
    let code = r as u32 * 65536 + g as u32 * 256 + b as u32;
    println!("{orange:?} -> #{code:06x}");

    let code: u32 = 0x33_66_a0;
    // as u8 은 아래 8비트만 남긴다
    let back = ((code / 65536) as u8, (code / 256) as u8, code as u8);
    println!("#{code:06x} -> {back:?}");

    let (r, g, b) = back;
    let sum = r as u32 + g as u32 + b as u32;
    println!("밝기 {:.1}", sum as f64 / 3.0);
}
