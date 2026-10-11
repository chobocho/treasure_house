use std::ops::{AddAssign, Mul, Neg};

#[derive(Debug, Clone, Copy)]
struct Vec2 {
    x: f64,
    y: f64,
}

// 오른쪽이 다른 타입이어도 된다 — 벡터 * 수.
impl Mul<f64> for Vec2 {
    type Output = Vec2;
    fn mul(self, k: f64) -> Vec2 {
        Vec2 {
            x: self.x * k,
            y: self.y * k,
        }
    }
}

// 단항 - .
impl Neg for Vec2 {
    type Output = Vec2;
    fn neg(self) -> Vec2 {
        Vec2 {
            x: -self.x,
            y: -self.y,
        }
    }
}

// += .
impl AddAssign for Vec2 {
    fn add_assign(&mut self, other: Vec2) {
        self.x += other.x;
        self.y += other.y;
    }
}

fn main() {
    let mut a = Vec2 { x: 1.0, y: 2.0 };
    println!("{:?} {:?}", a * 3.0, -a);
    a += Vec2 { x: 10.0, y: 10.0 };
    println!("{a:?}");
}
