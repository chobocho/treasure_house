// 제네릭 트레이트 — 한 타입에 여러 번 구현할 수 있다.
trait ConvertTo<T> {
    fn convert(&self) -> T;
}

struct Celsius(f64);

impl ConvertTo<f64> for Celsius {
    fn convert(&self) -> f64 {
        self.0
    }
}

impl ConvertTo<String> for Celsius {
    fn convert(&self) -> String {
        format!("{}도", self.0)
    }
}

fn main() {
    let c = Celsius(21.5);
    // 어느 구현인지 받는 타입으로 고른다.
    let n: f64 = c.convert();
    let s: String = c.convert();
    println!("{n} {s}");
}
