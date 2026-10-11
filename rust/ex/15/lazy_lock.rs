use std::collections::HashMap;
use std::sync::LazyLock;

// 처음 쓰일 때 한 번만 계산되는 전역 값.
static COLORS: LazyLock<HashMap<&str, u32>> = LazyLock::new(|| {
    println!("(표를 만든다)");
    HashMap::from([("red", 0xff0000), ("green", 0x00ff00)])
});

fn main() {
    println!("main 시작");
    println!("{:#08x}", COLORS["red"]);
    println!("{:#08x}", COLORS["green"]);
}
