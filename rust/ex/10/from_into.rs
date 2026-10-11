#[derive(Debug)]
struct Celsius(f64);

#[derive(Debug)]
struct Fahrenheit(f64);

// From 을 구현하면 Into 는 저절로 생긴다.
impl From<Celsius> for Fahrenheit {
    fn from(c: Celsius) -> Self {
        Fahrenheit(c.0 * 9.0 / 5.0 + 32.0)
    }
}

fn main() {
    let a = Fahrenheit::from(Celsius(100.0));
    let b: Fahrenheit = Celsius(0.0).into();
    println!("{a:?} {b:?} {}", a.0 - b.0);

    // 표준 라이브러리도 같은 방식이다.
    let s: String = "글자".into();
    let n = i64::from(7i32);
    println!("{s} {n}");
}
