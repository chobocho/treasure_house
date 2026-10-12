// 덧붙이는 부분을 맨 앞으로 옮겼다 — base = 값; 다음에 수들.
macro_rules! total {
    ($(base = $base:expr;)? $($x:expr),+ $(,)?) => {
        0 $(+ $base)? $(+ $x)+
    };
}

fn main() {
    println!("{}", total!(base = 100; 1, 2, 3));
}
//@ expect: error
