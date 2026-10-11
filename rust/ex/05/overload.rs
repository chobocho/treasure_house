fn area(side: u32) -> u32 {
    side * side
}

fn area(w: u32, h: u32) -> u32 {
    w * h
}

fn main() {
    println!("{} {}", area(3), area(3, 4));
}
//@ expect: E0428
