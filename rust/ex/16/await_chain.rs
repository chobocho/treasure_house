use std::future::Future;
use std::pin::pin;
use std::task::{Context, Poll, Waker};

fn block_on<F: Future>(future: F) -> F::Output {
    let mut future = pin!(future);
    let mut cx = Context::from_waker(Waker::noop());
    loop {
        if let Poll::Ready(value) = future.as_mut().poll(&mut cx) {
            return value;
        }
    }
}

async fn price(item: &str) -> u32 {
    println!("{item} 의 값을 알아본다");
    if item == "커피" { 4500 } else { 3000 }
}

async fn order() -> u32 {
    // .await — 그 퓨처가 끝날 때까지 기다렸다가 값을 받는다.
    let a = price("커피").await;
    let b = price("차").await;
    a + b
}

fn main() {
    println!("{}", block_on(order()));
}
