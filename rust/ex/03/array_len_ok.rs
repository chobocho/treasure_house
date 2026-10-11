fn main() {
    let rgb: [u8; 3] = [255, 128, 0];
    // 네 칸짜리를 새로 만들어 칸마다 옮긴다
    let rgba: [u8; 4] = [rgb[0], rgb[1], rgb[2], 255];
    println!("{rgba:?}");
}
