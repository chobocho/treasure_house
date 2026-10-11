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

fn main() {
    let name = String::from("ferris");
    // async 블록 — 그 자리에서 만드는 퓨처. 주변 변수를 붙잡는다.
    let greeting = async {
        println!("블록이 돈다");
        format!("안녕, {name}")
    };
    println!("아직 안 돌았다");
    println!("{}", block_on(greeting));
}
