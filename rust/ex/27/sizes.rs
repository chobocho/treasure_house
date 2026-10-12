use std::mem::size_of;

// 타입 이름과 그 크기를 한 줄로 찍는다.
macro_rules! show {
    ($($t:ty),*) => {
        $(print!("{} {}  ", stringify!($t), size_of::<$t>());)*
        println!();
    };
}

fn main() {
    show!(i8, i16, i32, i64, i128);
    show!(u8, usize, isize);
    show!(f32, f64, bool, char, ());
    show!(&u8, Box<u8>, Option<Box<u8>>);
    show!(&str, &[u8]);
    show!(String, Vec<u8>);
}
