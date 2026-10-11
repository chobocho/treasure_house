fn main() {
    let s = String::from("hello world");
    let whole: &String = &s;
    let world: &str = &s[6..];

    println!("&String {}바이트", size_of::<&String>());
    println!("&str    {}바이트", size_of::<&str>());
    println!("whole.len() = {}", whole.len());
    println!("world.len() = {}", world.len());
}
