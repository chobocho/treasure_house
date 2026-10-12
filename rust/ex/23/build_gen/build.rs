use std::env;
use std::fs;
use std::path::Path;

fn main() {
    println!("cargo::rerun-if-changed=colors.txt");
    let text = fs::read_to_string("colors.txt").unwrap();
    let names: Vec<&str> = text.lines().collect();
    // 줄 하나를 문자열 리터럴 하나로 바꿔 배열 하나를 적는다.
    let code = format!(
        "pub const COLORS: [&str; {}] = {:?};\n",
        names.len(),
        names
    );
    // 만든 소스는 Cargo 가 정해 준 디렉터리 OUT_DIR 에 둔다.
    let out_dir = env::var("OUT_DIR").unwrap();
    fs::write(Path::new(&out_dir).join("colors.rs"), code).unwrap();
}
