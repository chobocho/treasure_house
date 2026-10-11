enum List {
    Cons(i32, Box<List>),
    Nil,
}

use List::{Cons, Nil};

fn main() {
    let tail = Cons(5, Box::new(Cons(10, Box::new(Nil))));
    // 두 목록이 같은 꼬리를 함께 쓰고 싶다.
    let _a = Cons(3, Box::new(tail));
    let _b = Cons(4, Box::new(tail));
}
//@ expect: E0382
