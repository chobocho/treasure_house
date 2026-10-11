use std::thread;

fn main() {
    let numbers = vec![1, 2, 3, 4, 5, 6];
    let (left, right) = numbers.split_at(3);

    // scope 안에서 만든 스레드는 scope 가 끝나기 전에 반드시 끝난다.
    // 그래서 지역 변수를 move 없이 빌릴 수 있다.
    let (a, b) = thread::scope(|s| {
        let h1 = s.spawn(|| left.iter().sum::<i32>());
        let h2 = s.spawn(|| right.iter().sum::<i32>());
        (h1.join().unwrap(), h2.join().unwrap())
    });

    println!("{a} + {b} = {}", a + b);
    println!("numbers 는 그대로: {numbers:?}");
}
