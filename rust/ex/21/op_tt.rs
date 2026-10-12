// 연산자를 인자로 받아 보려 한다.
macro_rules! calc {
    ($a:expr, $op:tt, $b:expr) => {
        $a $op $b
    };
}

fn main() {
    println!("{}", calc!(6, +, 2));
}
