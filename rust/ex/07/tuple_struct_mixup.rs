struct Meters(f64);
struct Seconds(f64);

fn speed(d: Meters, t: Seconds) -> f64 {
    d.0 / t.0
}

fn main() {
    // 둘 다 속은 f64 지만 순서를 바꿔 넣으면 걸린다.
    println!("{}", speed(Seconds(9.58), Meters(100.0)));
}
//@ expect: E0308
