use std::sync::Mutex;
use std::thread;

fn main() {
    let words = ["rust", "is", "fun", "really"];
    let lengths = Mutex::new(Vec::new());

    // scope 안에서는 Arc 없이 Mutex 를 그대로 빌려 쓴다.
    thread::scope(|s| {
        for w in words {
            let lengths = &lengths;
            s.spawn(move || lengths.lock().unwrap().push(w.len()));
        }
    });

    let mut result = lengths.into_inner().unwrap();
    result.sort();
    println!("{result:?}");
}
