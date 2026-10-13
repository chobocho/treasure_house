use std::thread;

fn main() {
    let lines = vec![
        String::from("빨리 가려면 혼자 가고"),
        String::from("멀리 가려면 함께 가라"),
        String::from(""),
        String::from("천 리 길도 한 걸음부터"),
    ];

    // 줄마다 스레드 하나. 줄은 스레드로 옮겨 갔다가 수와 함께 돌아온다.
    let mut handles = Vec::new();
    for line in lines {
        handles.push(thread::spawn(move || {
            let words = line.split_whitespace().count();
            (line, words)
        }));
    }

    // 만든 차례대로 기다린다.
    let mut total = 0;
    for (i, handle) in handles.into_iter().enumerate() {
        let (line, words) = handle.join().unwrap();
        println!("{}번 줄 {words}낱말 [{line}]", i + 1);
        total += words;
    }
    println!("모두 {total}낱말");
}
