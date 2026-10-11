fn main() {
    let n = "42".parse::<i32>()?;
    println!("{n}");
}
//@ expect: E0277
