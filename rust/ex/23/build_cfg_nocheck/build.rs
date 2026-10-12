use std::env;

fn main() {
    // println! 으로 찍은 cargo:: 줄을 Cargo 가 읽는다.
    println!("cargo::rerun-if-env-changed=WITH_BANNER");
    if env::var("WITH_BANNER").is_ok() {
        println!("cargo::rustc-cfg=with_banner");
    }
}
