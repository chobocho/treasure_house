use std::thread;

fn main() {
    let mut handles = Vec::new();
    for id in 0..4 {
        handles.push(thread::spawn(move || id * id));
    }

    // 끝나는 순서는 알 수 없다.
    // 만든 순서대로 기다리면 결과의 순서는 정해진다.
    let results: Vec<i32> =
        handles.into_iter().map(|h| h.join().unwrap()).collect();
    println!("{results:?}");
}
