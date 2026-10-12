use std::sync::mpsc::{self, RecvTimeoutError};
use std::time::Duration;

fn main() {
    let limit = Duration::from_millis(10);
    let (tx, rx) = mpsc::channel();

    // 보낼 쪽은 살아 있는데 아무도 보내지 않는다.
    println!("{:?}", rx.recv_timeout(limit));

    tx.send("답").unwrap();
    println!("{:?}", rx.recv_timeout(limit)); // 이미 들어 있다

    drop(tx);
    let last = rx.recv_timeout(limit); // 보낼 쪽이 없다
    println!("{last:?}");
    println!("{}", last == Err(RecvTimeoutError::Disconnected));
}
