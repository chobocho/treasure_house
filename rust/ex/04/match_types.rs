fn main() {
    let n = 2;
    let text = match n {
        1 => "하나",
        2 => 2,
        _ => "많다",
    };
    println!("{text}");
}
//@ expect: E0308
