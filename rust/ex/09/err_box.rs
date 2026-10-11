use std::error::Error;

// Box<dyn Error> — "오류이기만 하면 무엇이든". 타입을 안 만든다.
fn ratio(a: &str, b: &str) -> Result<f64, Box<dyn Error>> {
    let x = a.parse::<i32>()?;
    let y = b.parse::<f64>()?;
    if y == 0.0 {
        return Err("0 으로 나눌 수 없다".into()); // 문자열도 된다
    }
    Ok(x as f64 / y)
}

fn main() {
    for (a, b) in
        [("1", "2.0"), ("하나", "2.0"), ("1", "둘"), ("1", "0")]
    {
        match ratio(a, b) {
            Ok(v) => println!("{v}"),
            Err(e) => println!("오류: {e}"),
        }
    }
}
