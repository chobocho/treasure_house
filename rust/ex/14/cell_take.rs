use std::cell::Cell;

fn main() {
    let name = Cell::new(String::from("kim"));
    println!("{}", name.take());
    // take 가 꺼내 간 자리에는 빈 String 이 남는다
    println!("{:?}", name.take());
    // replace 는 새 값을 넣고 있던 값을 돌려준다
    name.set(String::from("lee"));
    println!("{}", name.replace(String::from("park")));
    println!("{}", name.into_inner());
}
