macro_rules! square {
    ($x:expr) => {
        $x * $x
    };
}

fn main() {
    println!("{}", square!(3, 4));
}
//@ expect: error
