#[derive(Debug, Clone, Copy)]
struct Point {
    x: i32,
    y: i32,
}

#[derive(Debug, Clone)]
struct Player {
    name: String,
    at: Point,
}

fn main() {
    let a = Point { x: 1, y: 2 };
    let b = a; // Copy — 대입만으로 복사된다
    println!("{a:?} {b:?} {}", a.x + b.y);

    let p = Player {
        name: String::from("kim"),
        at: a,
    };
    let q = p.clone(); // Clone — 달라고 해야 복제한다
    println!("{p:?}\n{q:?}");
    println!("{} {}", q.name, q.at.x);
}
