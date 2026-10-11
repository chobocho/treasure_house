use std::sync::mpsc;

fn main() {
    let (tx, rx) = mpsc::channel::<i32>();
    tx.send(1).unwrap();
    drop(tx); // 보내는 쪽이 사라졌다

    println!("{:?}", rx.recv()); // 남아 있던 것은 받는다
    println!("{:?}", rx.recv()); // 그다음은 Err
}
