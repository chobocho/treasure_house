// 값이 패턴에 맞는지를 bool 로 준다.
macro_rules! is {
    ($value:expr, $p:pat) => {
        match $value {
            $p => true,
            _ => false,
        }
    };
}

fn main() {
    let port: Option<u16> = Some(443);
    println!("{}", is!(port, Some(_)));
    println!("{}", is!(port, Some(1..=1023)));
    println!("{}", is!(port, Some(80) | None));
    println!("{}", is!(7, 1 | 2 | 4));
}
