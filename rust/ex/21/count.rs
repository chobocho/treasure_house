// 받은 덩이의 수를 센다. 매크로가 자기 자신을 다시 부른다.
macro_rules! count {
    () => {
        0
    };
    ($head:tt $($tail:tt)*) => {
        1 + count!($($tail)*)
    };
}

fn main() {
    println!("{}", count!());
    println!("{}", count!(a));
    println!("{}", count!(a b c));
    println!("{}", count!((a b) [c d e] f));
}
