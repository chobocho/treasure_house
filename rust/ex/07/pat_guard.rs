enum Temp {
    Celsius(f64),
    Fahrenheit(f64),
}

fn is_freezing(t: &Temp) -> bool {
    match t {
        // 패턴으로 꺼낸 값에 조건을 더 건다(가드).
        Temp::Celsius(c) if *c <= 0.0 => true,
        Temp::Fahrenheit(f) if *f <= 32.0 => true,
        _ => false,
    }
}

fn main() {
    println!("{}", is_freezing(&Temp::Celsius(-3.0)));
    println!("{}", is_freezing(&Temp::Fahrenheit(50.0)));
}
