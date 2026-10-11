struct Counter {
    hits: u32,
}

impl Counter {
    // &mut self — 자기를 고친다.
    fn hit(&mut self) {
        self.hits += 1;
    }

    fn get(&self) -> u32 {
        self.hits
    }
}

fn main() {
    let mut c = Counter { hits: 0 };
    c.hit();
    c.hit();
    println!("{}", c.get());
}
