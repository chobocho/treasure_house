use std::rc::Rc;

fn main() {
    let shared = Rc::new(vec![1, 2, 3]);
    let _other = Rc::clone(&shared);
    shared.push(4);
}
//@ expect: E0596
