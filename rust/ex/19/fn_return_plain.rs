// 두 클로저 모두 아무것도 붙잡지 않는다.
fn pick(name: &str) -> impl Fn(i32) -> i32 {
    if name == "double" {
        |x| x * 2
    } else {
        |x| x + 1
    }
}

fn main() {
    println!("{}", pick("double")(5));
    println!("{}", pick("inc")(5));
    println!("{}", size_of_val(&pick("inc")));
}
