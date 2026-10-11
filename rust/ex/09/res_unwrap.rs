fn main() {
    let n: i32 = "42".parse().unwrap();
    println!("{n}");
    let m: i32 = "사십이".parse().unwrap();
    println!("{m}");
}
//@ exit: 101
