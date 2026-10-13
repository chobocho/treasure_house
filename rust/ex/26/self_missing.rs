struct Counter {
    n: u32,
}

impl Counter {
    fn show(&self) {
        println!("{}", self.n);
    }
}

fn main() {
    let c = Counter { n: 3 };
    c.show();
}
