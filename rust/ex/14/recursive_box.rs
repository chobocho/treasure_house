// Box 는 크기가 정해진 포인터다 — 그래서 List 의 크기도 정해진다.
enum List {
    Cons(i32, Box<List>),
    Nil,
}

use List::{Cons, Nil};

fn sum(list: &List) -> i32 {
    match list {
        Cons(value, rest) => value + sum(rest),
        Nil => 0,
    }
}

fn main() {
    let list =
        Cons(1, Box::new(Cons(2, Box::new(Cons(3, Box::new(Nil))))));
    println!("{}", sum(&list));
    println!("{} 바이트", std::mem::size_of::<List>());
}
