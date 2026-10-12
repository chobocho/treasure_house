use std::sync::Mutex;
use std::thread;

fn count_words(line: &str) -> usize {
    line.split_whitespace().count()
}

fn main() {
    let lines =
        ["to be or not to be", "that is the question", "says he"];
    let held = Mutex::new(0); // 잠근 채로 센다
    let brief = Mutex::new(0); // 세고 나서 잠근다

    thread::scope(|s| {
        for line in lines {
            let (held, brief) = (&held, &brief);
            s.spawn(move || {
                let mut total = held.lock().unwrap();
                *total += count_words(line); // 세는 동안 쥐고 있다
            });
            s.spawn(move || {
                let n = count_words(line); // 잠그지 않고 센다
                *brief.lock().unwrap() += n; // 더할 때만 잠근다
            });
        }
    });

    println!("잠근 채로 센 합: {}", held.into_inner().unwrap());
    println!("세고 나서 잠근 합: {}", brief.into_inner().unwrap());
}
