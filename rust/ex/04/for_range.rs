fn main() {
    for i in 0..3 {
        print!("{i} "); // 끝(3)은 들어가지 않는다
    }
    println!();
    for i in 1..=3 {
        print!("{i} "); // ..= 는 끝을 넣는다
    }
    println!();
}
