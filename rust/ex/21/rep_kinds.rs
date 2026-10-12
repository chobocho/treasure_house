// 수를 하나 이상 받아 더한다. 끝에 ; base = 값 을 덧붙일 수 있다.
macro_rules! total {
    ($($x:expr),+ $(,)? $(; base = $base:expr)?) => {
        0 $(+ $base)? $(+ $x)+
    };
}

fn main() {
    println!("{}", total!(1, 2, 3));
    println!("{}", total!(1, 2, 3,));
    println!("{}", total!(1, 2, 3; base = 100));
    println!("{}", total!(7));
}
