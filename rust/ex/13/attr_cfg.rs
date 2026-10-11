// cfg — 조건이 맞을 때만 컴파일에 넣는다.
#[cfg(target_os = "android")]
fn platform() -> &'static str {
    "android"
}

#[cfg(not(target_os = "android"))]
fn platform() -> &'static str {
    "그 밖"
}

fn main() {
    println!("{}", platform());
    println!("{}", cfg!(target_pointer_width = "64"));
}
