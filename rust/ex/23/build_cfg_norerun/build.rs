use std::env;

fn main() {
    // println! 으로 찍은 cargo:: 줄을 Cargo 가 읽는다.
    println!("cargo::rustc-check-cfg=cfg(with_banner)");
    if env::var("WITH_BANNER").is_ok() {
        println!("cargo::rustc-cfg=with_banner");
    }
}
