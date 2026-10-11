fn describe(input: &str) -> String {
    // if let 과 조건을 && 로 잇는다. 앞에서 꺼낸 값을 뒤에서 쓴다.
    if let Some((key, value)) = input.split_once('=')
        && let Ok(n) = value.parse::<u32>()
        && n > 0
    {
        format!("{key} 는 {n}")
    } else {
        format!("읽을 수 없다: {input}")
    }
}

fn main() {
    println!("{}", describe("port=8080"));
    println!("{}", describe("port=0"));
    println!("{}", describe("port"));
}
