// $( ... ),* — 쉼표로 나뉜 것이 몇 개든 받는다.
macro_rules! total {
    ($($x:expr),*) => {
        0 $(+ $x)*
    };
}

fn main() {
    println!("{}", total!());
    println!("{}", total!(1, 2, 3));
    println!("{}", total!(10, 20, 30, 40, 50));
}
