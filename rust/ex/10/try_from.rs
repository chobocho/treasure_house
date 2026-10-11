#[derive(Debug)]
struct Percent(u8);

// 실패할 수 있는 변환은 TryFrom — Result 를 돌려준다.
impl TryFrom<i32> for Percent {
    type Error = String;

    fn try_from(n: i32) -> Result<Self, String> {
        if (0..=100).contains(&n) {
            Ok(Percent(n as u8))
        } else {
            Err(format!("{n} 은 0~100 밖이다"))
        }
    }
}

fn main() {
    println!("{:?}", Percent::try_from(42));
    println!("{:?}", Percent::try_from(250));
    let p: Result<Percent, _> = (-1).try_into();
    println!("{p:?}");
    println!("{:?}", Percent::try_from(7).map(|p| p.0));
}
