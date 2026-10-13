use std::fmt;

struct Excerpt<'a> {
    part: &'a str,
}

impl fmt::Display for Excerpt<'_> {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "[{}]", self.part)
    }
}

fn main() {
    println!("{}", Excerpt { part: "rust" });
}
