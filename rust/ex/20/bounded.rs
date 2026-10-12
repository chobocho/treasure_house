use std::sync::mpsc::{
    self, Receiver, Sender, SyncSender, TrySendError,
};

fn main() {
    // channel() — 꺼내는 쪽이 없어도 send 는 받아 준다.
    let (tx, rx): (Sender<u32>, Receiver<u32>) = mpsc::channel();
    for n in 0..1000 {
        tx.send(n).unwrap();
    }
    drop(tx);
    println!("쌓여 있던 값: {}", rx.iter().count());

    // sync_channel(2) — 자리가 둘뿐이다.
    let (tx, rx): (SyncSender<u32>, Receiver<u32>) =
        mpsc::sync_channel(2);
    println!("{:?}", tx.try_send(1));
    println!("{:?}", tx.try_send(2));
    println!("{:?}", tx.try_send(3)); // 꽉 찼다
    if let Err(TrySendError::Full(back)) = tx.try_send(4) {
        println!("못 넣은 값을 돌려받았다: {back}");
    }

    println!("{:?}", rx.recv()); // 하나를 꺼내면
    println!("{:?}", tx.try_send(5)); // 자리가 난다
    println!("{:?}", rx.iter().take(2).collect::<Vec<_>>());

    drop(rx); // 받는 쪽이 사라지면
    println!("{:?}", tx.try_send(6));
}
