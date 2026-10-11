fn main() {
    let rgb: [u8; 3] = [255, 128, 0];
    // 네 칸짜리 배열 자리에 세 칸짜리를 넣는다
    let rgba: [u8; 4] = rgb;
    println!("{rgba:?}");
}
//@ expect: E0308
