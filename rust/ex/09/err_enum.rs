#[derive(Debug)]
enum ConfigError {
    Missing(String),
    BadNumber(String),
}

fn port(line: &str) -> Result<u16, ConfigError> {
    let value = line
        .strip_prefix("port=")
        .ok_or(ConfigError::Missing(String::from("port")))?;
    value
        .parse()
        .map_err(|_| ConfigError::BadNumber(value.to_string()))
}

fn main() {
    for line in ["port=8080", "host=a", "port=abc"] {
        match port(line) {
            Ok(p) => println!("포트 {p}"),
            Err(ConfigError::Missing(k)) => println!("{k} 항목이 없다"),
            Err(ConfigError::BadNumber(v)) => {
                println!("숫자가 아니다: {v}")
            }
        }
    }
}
