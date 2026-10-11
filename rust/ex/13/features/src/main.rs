// 기능(feature)이 켜졌을 때만 컴파일되는 함수.
#[cfg(feature = "fancy")]
fn decorate(s: &str) -> String {
    format!("*** {s} ***")
}

#[cfg(not(feature = "fancy"))]
fn decorate(s: &str) -> String {
    s.to_string()
}

fn main() {
    println!("{}", decorate("hello"));
}
