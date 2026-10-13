use std::ops::Add;

struct Won(u32);

impl Add for Won {
    type Output = Won;
    fn add(self, other: &Won) -> Won {
        Won(self.0 + other.0)
    }
}

fn main() {
    let sum = Won(300) + Won(500);
    println!("{}원", sum.0);
}
//@ expect: E0053
