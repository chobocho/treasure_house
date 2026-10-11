// 문자열 리터럴은 실행 파일 안에 들어 있다 — 프로그램 내내 산다.
fn greeting(formal: bool) -> &'static str {
    if formal {
        "안녕하십니까"
    } else {
        "안녕"
    }
}

static VERSION: &str = "1.0";

fn main() {
    let g: &'static str = greeting(true);
    println!("{g} (v{VERSION})");
}
