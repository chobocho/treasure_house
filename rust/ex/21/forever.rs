// 받은 것을 줄이지 않고 그대로 자기를 다시 부른다.
macro_rules! forever {
    ($($t:tt)*) => {
        forever!($($t)*)
    };
}

fn main() {
    forever!(a b c);
}
//@ expect: error
