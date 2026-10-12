use std::sync::Mutex;
use std::thread;

// 약속: 두 벡터의 길이는 늘 같다.
struct Table {
    names: Vec<&'static str>,
    scores: Vec<u32>,
}

fn main() {
    let table = Mutex::new(Table {
        names: vec!["가"],
        scores: vec![90],
    });

    thread::scope(|s| {
        let worker = s.spawn(|| {
            let mut t = table.lock().unwrap();
            t.names.push("나");
            let score: u32 = "여든".parse().unwrap(); // 여기서 패닉
            t.scores.push(score);
        });
        let _ = worker.join();
    });

    // 독이 든 잠금에서도 열쇠를 꺼낼 수 있다.
    let mut t = table.lock().unwrap_or_else(|e| e.into_inner());
    println!("이름 {} 개, 점수 {} 개", t.names.len(), t.scores.len());
    t.names.pop(); // 하다 만 일을 되돌린다
    println!("이름 {} 개, 점수 {} 개", t.names.len(), t.scores.len());
    drop(t);

    println!("lock 이 Ok 인가: {}", table.lock().is_ok());
    table.clear_poison(); // 고쳤으니 독을 지운다
    println!("lock 이 Ok 인가: {}", table.lock().is_ok());
}
