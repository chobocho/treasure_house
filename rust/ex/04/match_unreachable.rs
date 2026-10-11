fn main() {
    let n = 5;
    let text = match n {
        _ => "아무거나",
        5 => "다섯",
    };
    println!("{text}");
}
//@ warnings: show
