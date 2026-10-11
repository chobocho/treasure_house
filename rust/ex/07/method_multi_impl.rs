struct Temp {
    celsius: f64,
}

// 만드는 것.
impl Temp {
    fn from_celsius(c: f64) -> Self {
        Self { celsius: c }
    }
}

// 바꿔 보는 것. impl 블록은 여럿으로 나눠도 된다.
impl Temp {
    fn fahrenheit(&self) -> f64 {
        self.celsius * 9.0 / 5.0 + 32.0
    }

    fn is_freezing(&self) -> bool {
        self.celsius <= 0.0
    }
}

fn main() {
    let t = Temp::from_celsius(-5.0);
    println!("{} {}", t.fahrenheit(), t.is_freezing());
}
