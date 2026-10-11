use std::cell::RefCell;
use std::rc::{Rc, Weak};

struct Node {
    name: &'static str,
    parent: RefCell<Weak<Node>>, // 부모는 약하게 가리킨다
    children: RefCell<Vec<Rc<Node>>>, // 자식은 부모가 가진다
}

impl Drop for Node {
    fn drop(&mut self) {
        println!("{} 정리", self.name);
    }
}

fn node(name: &'static str) -> Rc<Node> {
    Rc::new(Node {
        name,
        parent: RefCell::new(Weak::new()),
        children: RefCell::new(Vec::new()),
    })
}

fn main() {
    let root = node("뿌리");
    let leaf = node("잎");
    root.children.borrow_mut().push(Rc::clone(&leaf));
    *leaf.parent.borrow_mut() = Rc::downgrade(&root);

    let parent = leaf.parent.borrow().upgrade();
    println!("잎의 부모: {}", parent.map(|p| p.name).unwrap_or("없음"));
    println!("뿌리의 자식 {}개", root.children.borrow().len());
    println!("main 끝");
}
