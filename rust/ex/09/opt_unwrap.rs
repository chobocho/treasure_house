fn main() {
    let some: Option<i32> = Some(5);
    let none: Option<i32> = None;
    println!("{}", some.unwrap());
    println!("{}", none.unwrap());
}
//@ exit: 101
