// 새 조각 종류를 enum 에 더했는데 match 한 곳을 깜빡했다.
#[derive(Clone, Copy)]
enum Kind {
    I,
    O,
    T,
}

fn box_size(k: Kind) -> i32 {
    match k {
        Kind::I => 4,
        Kind::O => 2,
    }
}

fn main() {
    println!("{}", box_size(Kind::T));
}
