// 같은 패키지의 라이브러리를 패키지 이름으로 가져다 쓴다.
use greeter::greet;

fn main() {
    println!("{}", greet("  Ferris "));
}
