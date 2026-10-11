fn kib(n: usize) -> usize {
    n * 1024
}

const BUFFER: usize = kib(4);

fn main() {
    println!("{BUFFER}");
}
//@ expect: E0015
