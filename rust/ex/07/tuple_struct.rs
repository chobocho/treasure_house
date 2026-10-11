// 필드에 이름이 없는 구조체. 타입에 이름을 주는 것이 목적이다.
struct Point(i32, i32);
struct Meters(f64);
struct Seconds(f64);

fn speed(d: Meters, t: Seconds) -> f64 {
    d.0 / t.0
}

fn main() {
    let p = Point(3, 4);
    println!("{} {}", p.0, p.1);
    println!("{}", speed(Meters(100.0), Seconds(9.58)) > 10.0);
}
