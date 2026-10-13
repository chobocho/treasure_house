use std::fmt;

#[derive(Debug)]
struct Won(u32);

impl fmt::Debug for Won {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "{}원", self.0)
    }
}

fn main() {
    println!("{:?}", Won(500));
}
//@ expect: E0119
