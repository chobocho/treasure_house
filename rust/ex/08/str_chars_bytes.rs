fn main() {
    let s = "a가";

    for c in s.chars() {
        print!("{c:?} "); // 글자(char) 단위
    }
    println!();
    for b in s.bytes() {
        print!("{b:#04x} "); // 바이트(u8) 단위
    }
    println!();
    for (i, c) in s.char_indices() {
        print!("{i}:{c} "); // 글자와, 그 글자가 시작하는 바이트 자리
    }
    println!();
}
