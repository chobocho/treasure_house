use std::cell::RefCell;

struct Counter {
    name: String,
    hits: RefCell<u32>,
}

impl Counter {
    // &self 인데도 안의 값을 고친다 — 내부 가변성.
    fn visit(&self) -> String {
        *self.hits.borrow_mut() += 1;
        format!("{} {}번째", self.name, self.hits.borrow())
    }
}

fn main() {
    let c = Counter {
        name: String::from("방문"),
        hits: RefCell::new(0),
    };
    println!("{}", c.visit());
    println!("{}", c.visit());
}
