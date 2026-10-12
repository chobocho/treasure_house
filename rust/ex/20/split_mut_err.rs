use std::thread;

fn main() {
    let mut buf = vec![0u64; 10];

    thread::scope(|s| {
        // 두 스레드가 벡터의 앞 절반과 뒤 절반을 채우려 한다.
        s.spawn(|| {
            for i in 0..5 {
                buf[i] = (i * i) as u64;
            }
        });
        s.spawn(|| {
            for i in 5..10 {
                buf[i] = (i * i) as u64;
            }
        });
    });
    println!("{buf:?}");
}
//@ expect: E0499
