fn main() {
    let port: Option<u16> = Some(443);
    let none: Option<u16> = None;

    println!("{} {}", port.is_some(), none.is_none());
    println!("{}", port.is_some_and(|p| p < 1024));
    println!("{:?}", port.filter(|p| *p > 1024));
    println!("{:?}", none.or(Some(80)));
}
