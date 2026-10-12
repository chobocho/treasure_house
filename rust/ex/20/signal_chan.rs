use std::sync::mpsc;
use std::thread;

fn main() {
    let (done_tx, done_rx) = mpsc::channel::<()>();

    // 받을 쪽이 기다리기 전에 신호를 보내고 끝난다.
    thread::scope(|s| {
        s.spawn(move || {
            done_tx.send(()).unwrap(); // 다 됐다
        });
    });

    // 신호는 채널에 남아 있다.
    println!("{:?}", done_rx.recv());
    // 보낼 쪽이 사라진 것도 신호다.
    println!("{:?}", done_rx.recv());
}
