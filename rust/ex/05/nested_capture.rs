fn main() {
    let factor = 3;
    fn scale(x: i32) -> i32 {
        x * factor
    }
    println!("{}", scale(7));
}
//@ expect: E0434
