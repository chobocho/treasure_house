// 경로는 이 소스 파일이 있는 디렉터리(src/)에서 본 것이다.
const MOTTO: &str = include_str!("motto.txt");
const RAW: &[u8] = include_bytes!("motto.txt");

fn main() {
    print!("{MOTTO}");
    println!("바이트 {}개, 처음 셋 {:?}", RAW.len(), &RAW[..3]);
}
