use std::env;

fn main() {
    // 환경 변수는 있을 수도, 없을 수도 있다
    let mode = env::var("APP_MODE");
    println!("{mode:?}");

    // 없으면 기본값을 쓴다
    let mode = mode.unwrap_or_else(|_| String::from("normal"));
    println!("mode = {mode:?}");

    // 값은 글이다. 수로 쓰려면 parse 한다
    let jobs: u32 = env::var("APP_JOBS")
        .ok()
        .and_then(|s| s.parse().ok())
        .unwrap_or(1);
    println!("jobs = {jobs}");
}
