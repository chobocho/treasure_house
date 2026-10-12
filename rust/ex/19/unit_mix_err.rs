use std::ops::Add;

#[derive(Debug, Clone, Copy)]
struct Meters(f64);

#[derive(Debug, Clone, Copy)]
struct Feet(f64);

// 같은 단위끼리만 더한다.
impl Add for Meters {
    type Output = Meters;

    fn add(self, rhs: Meters) -> Meters {
        Meters(self.0 + rhs.0)
    }
}

fn main() {
    let runway = Meters(1200.0);
    let taxi = Feet(300.0);
    println!("{:?}", runway + taxi);
}
//@ expect: E0308
