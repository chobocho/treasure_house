struct Point {
    x: i32,
    y: i32,
}

// 매개변수 자리도 패턴이다.
fn sum((a, b): (i32, i32)) -> i32 {
    a + b
}

fn norm1(&Point { x, y }: &Point) -> i32 {
    x.abs() + y.abs()
}

fn main() {
    println!("{}", sum((3, 4)));
    println!("{}", norm1(&Point { x: -3, y: 4 }));

    let pairs = [(1, 'a'), (2, 'b')];
    for (n, c) in pairs {
        print!("{n}{c} "); // for 의 변수 자리도
    }
    // 클로저의 매개변수도
    let total: i32 = pairs.iter().map(|(n, _)| n).sum();
    println!("{total}");
}
