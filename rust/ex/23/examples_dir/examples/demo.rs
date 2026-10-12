// examples/ 의 파일 — 라이브러리를 바깥 사용자처럼 가져다 쓴다.
use greet::line;

fn main() {
    println!("demo: {}", line("hi", "example"));
}
