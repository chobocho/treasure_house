use std::pin::pin;
use std::task::{Context, Waker};

fn main() {
    let mut cx = Context::from_waker(Waker::noop());

    // pin! 은 값을 가져가 이 블록 안에 고정하고, Pin<&mut …> 를 내준다.
    let future = async { 42 };
    let mut pinned = pin!(future);
    let answer = pinned.as_mut().poll(&mut cx);
    println!("pin!: {answer:?}");
    let _elsewhere = future;

    // Box::pin 은 값을 힙에 고정하고, Pin<Box<…>> 를 내준다.
    let mut boxed = Box::pin(async { 7 });
    let answer = boxed.as_mut().poll(&mut cx);
    println!("Box::pin: {answer:?}");
}
//@ expect: E0382
