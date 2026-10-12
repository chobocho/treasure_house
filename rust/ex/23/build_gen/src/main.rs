// build.rs 가 만든 파일을 이 자리에 소스로 끼워 넣는다.
include!(concat!(env!("OUT_DIR"), "/colors.rs"));

fn main() {
    println!("{}가지: {}", COLORS.len(), COLORS.join(" "));
}
