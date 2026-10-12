// 이름에 따라 다른 클로저를 돌려주려 한다.
fn pick(name: &str, by: i32) -> impl Fn(i32) -> i32 {
    if name == "add" {
        move |x| x + by
    } else {
        move |x| x * by
    }
}

fn main() {
    println!("{}", pick("add", 3)(5));
    println!("{}", pick("mul", 3)(5));
}
//@ expect: E0308
