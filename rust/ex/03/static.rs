// static 도 타입을 적고, 값은 컴파일할 때 정해진다
static GREETING: &str = "안녕하세요";
static VERSION: u32 = 3;

fn main() {
    println!("{GREETING}, 버전 {VERSION}");
    show();
}

// 프로그램 어디에서나 같은 이름으로 읽는다
fn show() {
    println!("show 에서도: 버전 {VERSION}");
}
