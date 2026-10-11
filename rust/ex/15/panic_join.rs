use std::thread;

fn main() {
    let handle = thread::spawn(|| {
        panic!("일꾼이 쓰러졌다");
    });

    // 다른 스레드의 패닉은 join 의 Err 로 돌아온다.
    let result = handle.join();
    println!("실패했나: {}", result.is_err());
    println!("main 은 계속 간다");
}
