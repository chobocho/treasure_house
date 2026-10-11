#[derive(Debug)]
struct Point<T> {
    x: T,
    y: T,
}

// 타입 인자가 둘이면 서로 다른 타입을 담을 수 있다.
#[derive(Debug)]
struct Pair<A, B> {
    left: A,
    right: B,
}

fn main() {
    let a = Point { x: 1, y: 2 };
    let b = Point { x: 0.5, y: 1.5 };
    let c = Pair {
        left: "나이",
        right: 31,
    };
    println!("{a:?} {b:?} {c:?}");
    println!("{} {} {}", a.x + a.y, b.x + b.y, c.left.len() + c.right);
}
