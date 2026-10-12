use std::pin::Pin;
use std::task::{Context, Waker};

fn main() {
    let mut cx = Context::from_waker(Waker::noop());
    let mut future = async { 42 };
    let answer = Pin::new(&mut future).poll(&mut cx);
    println!("{answer:?}");
}
//@ expect: E0277
