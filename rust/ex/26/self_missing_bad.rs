struct Counter {
    n: u32,
}

impl Counter {
    fn show() {
        println!("{}", self.n);
    }
}

fn main() {
    let c = Counter { n: 3 };
    c.show();
}
//@ expect: E0424,E0599
