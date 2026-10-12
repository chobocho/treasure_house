const WIDTH: usize = 4;

fn blank<const N: usize>() -> [u8; N] {
    [b'.'; N]
}

fn main() {
    let c = blank::<WIDTH * 2 + 1>();
    println!("{}", c.len());
}
//@ expect: error
