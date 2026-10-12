// frame 이 켜졌을 때만 있는 함수와, 꺼졌을 때만 있는 함수.
#[cfg(feature = "frame")]
fn frame(s: &str) -> String {
    format!("[ {s} ]")
}

#[cfg(not(feature = "frame"))]
fn frame(s: &str) -> String {
    s.to_string()
}

fn main() {
    // cfg! 는 같은 조건을 bool 값으로 준다.
    let text = if cfg!(feature = "shout") {
        "HELLO"
    } else {
        "hello"
    };
    println!("{}", frame(text));
    println!(
        "frame={} shout={} loud={}",
        cfg!(feature = "frame"),
        cfg!(feature = "shout"),
        cfg!(feature = "loud")
    );
}
