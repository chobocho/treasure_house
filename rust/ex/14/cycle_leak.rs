use std::cell::RefCell;
use std::rc::Rc;

struct Node {
    name: &'static str,
    next: RefCell<Option<Rc<Node>>>,
}

impl Drop for Node {
    fn drop(&mut self) {
        println!("{} 정리", self.name);
    }
}

fn main() {
    let a = Rc::new(Node {
        name: "a",
        next: RefCell::new(None),
    });
    let b = Rc::new(Node {
        name: "b",
        next: RefCell::new(None),
    });
    *a.next.borrow_mut() = Some(Rc::clone(&b)); // a → b
    *b.next.borrow_mut() = Some(Rc::clone(&a)); // b → a : 고리가 됐다

    println!("a {} / b {}", Rc::strong_count(&a), Rc::strong_count(&b));
    println!("main 끝");
} // "정리" 가 한 번도 찍히지 않는다
