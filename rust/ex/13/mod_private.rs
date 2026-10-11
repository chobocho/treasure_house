mod geometry {
    fn double(n: u32) -> u32 {
        n * 2
    }
}

fn main() {
    println!("{}", geometry::double(7));
}
//@ expect: E0603
