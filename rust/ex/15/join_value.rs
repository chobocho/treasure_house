use std::thread;

fn main() {
    let handle = thread::spawn(|| {
        let mut total: u64 = 0;
        for n in 1..=1_000_000 {
            total += n;
        }
        total // 클로저의 값이 스레드의 결과가 된다
    });

    println!("기다리는 동안 main 은 다른 일을 할 수 있다");
    let total = handle.join().unwrap();
    println!("{total}");
}
