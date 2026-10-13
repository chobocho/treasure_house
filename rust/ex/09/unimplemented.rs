fn area(shape: &str, side: u32) -> u32 {
    if shape == "square" {
        side * side
    } else {
        // 다른 도형은 만들지 않기로 했다
        unimplemented!("{shape} 의 넓이")
    }
}

fn main() {
    println!("{}", area("square", 3));
    println!("{}", area("circle", 3));
}
//@ exit: 101
