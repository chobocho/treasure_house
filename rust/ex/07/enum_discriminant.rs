// 데이터 없는 열거형은 정수로 바꿀 수 있다. 번호를 직접 줄 수도 있다.
#[derive(Clone, Copy)]
enum Status {
    Ok = 200,
    NotFound = 404,
    Teapot = 418,
}

enum Level {
    Low, // 0 부터 차례로
    Mid,
    High,
}

fn main() {
    println!("{} {}", Status::Ok as u16, Status::Teapot as u16);
    println!("{}", Status::NotFound as u16 + 1);
    println!(
        "{} {} {}",
        Level::Low as u8,
        Level::Mid as u8,
        Level::High as u8
    );
}
