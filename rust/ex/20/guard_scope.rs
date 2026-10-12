use std::sync::Mutex;

fn main() {
    let jobs = Mutex::new(vec![1, 2]);

    // let 문 — 열쇠는 그 문이 끝날 때 사라진다.
    let job = jobs.lock().unwrap().pop();
    let held = jobs.try_lock().is_err();
    println!("let 다음 줄: 일 {job:?}, 잠겨 있나 {held}");

    // while let 의 머리에서 잠그면 몸통에서도 잠겨 있다.
    while let Some(job) = jobs.lock().unwrap().pop() {
        let held = jobs.try_lock().is_err();
        println!("while let 몸통: 일 {job}, 잠겨 있나 {held}");
    }

    jobs.lock().unwrap().push(3);
    // 꺼내는 일을 let 문으로 떼어 낸다.
    loop {
        let job = jobs.lock().unwrap().pop();
        let Some(job) = job else { break };
        let held = jobs.try_lock().is_err();
        println!("loop 몸통: 일 {job}, 잠겨 있나 {held}");
    }
}
