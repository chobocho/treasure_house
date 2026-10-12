use std::pin::pin;
use std::task::{Context, Waker};

async fn launch() -> &'static str {
    "발사"
}

fn main() {
    let mut future = pin!(launch());
    let mut cx = Context::from_waker(Waker::noop());
    for turn in 1..=2 {
        let answer = future.as_mut().poll(&mut cx);
        println!("{turn}번째 poll: {answer:?}");
    }
}
//@ exit: 101
