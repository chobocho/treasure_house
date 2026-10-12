// 받은 것에 2 를 곱한다.
macro_rules! double {
    ($x:expr) => {
        $x * 2
    };
}

fn main() {
    println!("{}", double!(5));
    println!("{}", double!("ab"));
}
//@ expect: E0369
