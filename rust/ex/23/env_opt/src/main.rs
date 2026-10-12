fn main() {
    // 없을 수도 있는 변수는 option_env! 로 읽는다.
    let greeting: Option<&'static str> = option_env!("GREETING");
    match greeting {
        Some(g) => println!("빌드할 때 GREETING 은 {g}"),
        None => println!("빌드할 때 GREETING 이 없었다"),
    }
}
