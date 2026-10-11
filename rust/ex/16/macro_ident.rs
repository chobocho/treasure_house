// ident — 이름을 받는다. 받은 이름으로 함수를 만들어 낸다.
macro_rules! make_adder {
    ($name:ident, $n:expr) => {
        fn $name(x: i32) -> i32 {
            x + $n
        }
    };
}

make_adder!(add_one, 1);
make_adder!(add_ten, 10);

fn main() {
    println!("{} {}", add_one(5), add_ten(5));
}
