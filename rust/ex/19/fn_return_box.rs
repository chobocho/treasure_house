// 서로 다른 클로저를 같은 타입의 상자에 담아 돌려준다.
fn pick(name: &str, by: i32) -> Box<dyn Fn(i32) -> i32> {
    match name {
        "double" => Box::new(|x| x * 2),
        "add" => Box::new(move |x| x + by),
        _ => Box::new(i32::abs),
    }
}

fn main() {
    println!("{}", pick("double", 0)(5));
    println!("{}", pick("add", 3)(5));
    println!("{}", pick("other", 0)(-5));
}
