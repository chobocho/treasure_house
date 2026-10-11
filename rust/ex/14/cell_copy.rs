use std::cell::Cell;

struct Counter {
    hits: Cell<u32>,
}

impl Counter {
    fn visit(&self) -> u32 {
        // Cell 은 빌려주지 않는다 — 통째로 꺼내고(get) 넣는다(set).
        self.hits.set(self.hits.get() + 1);
        self.hits.get()
    }
}

fn main() {
    let c = Counter { hits: Cell::new(0) };
    c.visit();
    println!("{}", c.visit());
}
