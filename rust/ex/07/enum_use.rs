#[derive(Debug)]
enum Light {
    Red,
    Yellow,
    Green,
}

// 변형 이름을 끌어오면 Light:: 를 안 써도 된다.
use Light::{Green, Red, Yellow};

fn next(l: Light) -> Light {
    match l {
        Red => Green,
        Green => Yellow,
        Yellow => Red,
    }
}

fn main() {
    let l = next(next(Red));
    println!("{l:?}");
}
