use std::thread;

fn main() {
    // spawn 은 새 스레드에서 클로저를 돌리고 손잡이를 돌려준다.
    let handle = thread::spawn(|| {
        println!("새 스레드에서 일한다");
    });

    handle.join().unwrap(); // 그 스레드가 끝날 때까지 기다린다
    println!("main 이 이어서 한다");
}
