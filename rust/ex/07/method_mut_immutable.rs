struct Counter {
    hits: u32,
}

impl Counter {
    fn hit(&mut self) {
        self.hits += 1;
    }
}

fn main() {
    let c = Counter { hits: 0 };
    c.hit();
    println!("{}", c.hits);
}
//@ expect: E0596
