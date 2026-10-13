use std::thread;

fn main() {
    let mut n = 21; // i32 는 Copy 다
    let handle = thread::spawn(move || {
        // 스레드가 가져간 것은 복사본이다
        n += 1;
        n
    });
    let inside = handle.join().unwrap();
    // 넘긴 뒤에도 main 의 n 을 쓴다
    println!("{n} {inside}");
}
