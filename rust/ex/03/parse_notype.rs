fn main() {
    // 어떤 타입으로 읽을지 어디에도 적지 않았다
    let n = "42".parse().expect("수가 아니다");
    println!("{n}");
}
//@ expect: E0284
