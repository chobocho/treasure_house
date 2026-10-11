use std::sync::RwLock;

fn main() {
    let config = RwLock::new(String::from("v1"));
    {
        // 읽는 잠금은 여럿이 함께 잡을 수 있다.
        let a = config.read().unwrap();
        let b = config.read().unwrap();
        println!("{a} {b}");
    }
    // 쓰는 잠금은 혼자만.
    config.write().unwrap().push_str("-patched");
    println!("{}", config.read().unwrap());
}
