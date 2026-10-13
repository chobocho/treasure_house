struct Excerpt<'a> {
    part: &'a str,
}

impl Excerpt<'a> {
    fn len(&self) -> usize {
        self.part.len()
    }
}

fn main() {
    let e = Excerpt { part: "rust" };
    println!("{}", e.len());
}
//@ expect: E0261
