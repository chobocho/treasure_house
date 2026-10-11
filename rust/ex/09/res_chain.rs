fn parse_port(s: &str) -> Result<u16, String> {
    s.trim()
        .parse::<u16>()
        .map_err(|e| format!("포트 `{s}`: {e}"))
        .and_then(|p| {
            if p == 0 {
                Err(String::from("포트 0 은 쓸 수 없다"))
            } else {
                Ok(p)
            }
        })
}

fn main() {
    println!("{:?}", parse_port(" 8080 "));
    println!("{:?}", parse_port("0"));
    println!("{:?}", parse_port("99999"));
}
