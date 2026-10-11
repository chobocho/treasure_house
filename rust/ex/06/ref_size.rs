fn main() {
    let s = String::from("hello");
    let r = &s;
    let r2 = &s; // 읽기만 하는 참조는 여럿 만들 수 있다

    println!("String  {}바이트", size_of::<String>());
    println!("&String {}바이트", size_of::<&String>());
    println!("{r} {r2}");
}
