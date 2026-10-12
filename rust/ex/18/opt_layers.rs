use std::num::ParseIntError;

// 없어도 되는 설정이지만, 적었다면 수여야 한다
fn port(text: Option<&str>) -> Result<Option<u16>, ParseIntError> {
    text.map(|s| s.parse::<u16>()).transpose()
}

fn main() {
    // map 만 하면 Option 안에 Result 가 든다
    println!("{:?}", Some("8080").map(|s| s.parse::<u16>()));

    // transpose — 안팎을 바꾼다
    println!("{:?}", port(Some("8080")));
    println!("{:?}", port(None));
    println!("{:?}", port(Some("http")));

    // flatten — 겹친 Option 을 한 겹으로
    let seats = [Some("kim"), None, Some("lee")];
    // get 은 칸이 없으면 None, 칸이 비었으면 Some(None) 이다
    println!("{:?}", seats.get(0).copied());
    println!("{:?}", seats.get(1).copied());
    println!("{:?}", seats.get(9).copied());
    println!("{:?}", seats.get(0).copied().flatten());
    println!("{:?}", seats.get(1).copied().flatten());
    println!("{:?}", seats.get(9).copied().flatten());
}
