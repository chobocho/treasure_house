use std::ops::Add;

#[derive(Debug, Clone, Copy)]
struct Meters(f64);

#[derive(Debug, Clone, Copy)]
struct Feet(f64);

impl Add for Meters {
    type Output = Meters;

    fn add(self, rhs: Meters) -> Meters {
        Meters(self.0 + rhs.0)
    }
}

// 단위를 바꾸는 길은 이 구현 하나뿐이다.
impl From<Feet> for Meters {
    fn from(ft: Feet) -> Meters {
        Meters(ft.0 * 0.3048)
    }
}

fn main() {
    let runway = Meters(1200.0);
    let taxi = Feet(300.0);
    // 바꾸겠다고 적어야 더해진다.
    let total = runway + Meters::from(taxi);
    println!("{total:.2?}");
    let again: Meters = taxi.into();
    println!("{:.2?}", runway + again + again);
}
