use std::sync::atomic::{AtomicBool, AtomicU32, Ordering};

fn main() {
    let n = AtomicU32::new(5); // mut 가 없다
    println!("load: {}", n.load(Ordering::SeqCst));

    n.store(7, Ordering::SeqCst);
    println!("store(7) 뒤: {}", n.load(Ordering::SeqCst));

    // 나머지 셋은 바꾸면서 바꾸기 전의 값을 돌려준다.
    let old = n.swap(10, Ordering::SeqCst);
    println!("swap(10) 이 돌려준 값: {old}");
    let old = n.fetch_add(1, Ordering::SeqCst);
    println!("fetch_add(1) 이 돌려준 값: {old}");
    let old = n.fetch_sub(4, Ordering::SeqCst);
    println!("fetch_sub(4) 가 돌려준 값: {old}");
    println!("지금: {}", n.load(Ordering::SeqCst));

    // 깃발 — swap 이 돌려준 값으로 "내가 처음인가" 를 안다.
    let started = AtomicBool::new(false);
    let first = started.swap(true, Ordering::SeqCst);
    let second = started.swap(true, Ordering::SeqCst);
    println!("이미 서 있었나: {first}, 다시 물으면: {second}");
}
