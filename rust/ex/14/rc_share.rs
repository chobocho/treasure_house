use std::rc::Rc;

enum List {
    Cons(i32, Rc<List>),
    Nil,
}

use List::{Cons, Nil};

fn sum(list: &List) -> i32 {
    match list {
        Cons(v, rest) => v + sum(rest),
        Nil => 0,
    }
}

fn main() {
    let tail = Rc::new(Cons(5, Rc::new(Cons(10, Rc::new(Nil)))));
    // Rc::clone 은 값을 복사하지 않는다 — 주인 수만 하나 늘린다.
    let a = Cons(3, Rc::clone(&tail));
    let b = Cons(4, Rc::clone(&tail));
    println!("{} {}", sum(&a), sum(&b));
    println!("주인 {}명", Rc::strong_count(&tail));
}
