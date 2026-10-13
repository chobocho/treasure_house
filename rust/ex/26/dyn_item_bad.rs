fn doubles(limit: u32) -> Box<dyn Iterator> {
    Box::new((1..=limit).map(|n| n * 2))
}

fn main() {
    let v: Vec<u32> = doubles(3).collect();
    println!("{v:?}");
}
//@ expect: E0191
