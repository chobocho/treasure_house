use std::cell::RefCell;
use std::thread;

thread_local! {
    // 이 스레드가 한 일을 적어 두는 일지
    static LOG: RefCell<Vec<String>> = RefCell::new(Vec::new());
}

// 일지를 인자로 받지 않는다 — 부른 스레드의 것에 적는다.
fn note(text: &str) {
    LOG.with(|log: &RefCell<Vec<String>>| {
        log.borrow_mut().push(text.to_string());
    });
}

fn load(name: &str) -> usize {
    note(&format!("{name} 읽기"));
    name.chars().count()
}

fn job(names: &[&str]) -> (usize, Vec<String>, usize) {
    let mut total = 0;
    for name in names {
        total += load(name);
    }
    note("끝");
    let log = LOG.take(); // 일지를 통째로 꺼낸다
    let left = LOG.with_borrow(|log| log.len());
    (total, log, left)
}

fn main() {
    note("시작");
    let a = thread::spawn(|| job(&["사과", "배"]));
    let b = thread::spawn(|| job(&["복숭아", "감"]));
    println!("{:?}", a.join().unwrap());
    println!("{:?}", b.join().unwrap());

    // main 의 일지에는 main 이 적은 것만 있다.
    let n = LOG.with(|log| log.borrow().len());
    let same = LOG.with_borrow(|log| log.len());
    let mine = LOG.take();
    println!("main 의 일지: {n} 줄, {same} 줄 {mine:?}");
}
