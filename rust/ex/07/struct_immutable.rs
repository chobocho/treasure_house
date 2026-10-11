struct Counter {
    hits: u32,
}

fn main() {
    let c = Counter { hits: 0 };
    c.hits += 1;
    println!("{}", c.hits);
}
//@ expect: E0594
