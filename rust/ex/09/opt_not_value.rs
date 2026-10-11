fn main() {
    let maybe: Option<i32> = Some(5);
    let total = maybe + 1;
    println!("{total}");
}
//@ expect: E0369
