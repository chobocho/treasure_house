fn main() {
    let maybe: Option<i32> = Some(5);
    let Some(n) = maybe;
    println!("{n}");
}
//@ expect: E0005
