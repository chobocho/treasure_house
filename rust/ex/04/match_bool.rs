fn main() {
    let ready = true;
    // bool 은 두 값뿐이라 _ 없이도 전부 다룬 것이다.
    let msg = match ready {
        true => "출발",
        false => "대기",
    };
    println!("{msg}");
}
