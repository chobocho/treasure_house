use std::future::Future;
use std::pin::pin;
use std::task::{Context, Poll, Waker};

// 퓨처 하나를 끝날 때까지 돌리는 가장 작은 실행기.
fn block_on<F: Future>(future: F) -> F::Output {
    let mut future = pin!(future);
    let mut cx = Context::from_waker(Waker::noop());
    loop {
        // poll — "다 됐나?" 하고 물어 한 걸음 진행시킨다.
        if let Poll::Ready(value) = future.as_mut().poll(&mut cx) {
            return value;
        }
    }
}

async fn fetch() -> u32 {
    println!("fetch 가 돈다");
    42
}

fn main() {
    let future = fetch(); // 아직 아무 일도 없다
    println!("퓨처를 만들었다");
    println!("{}", block_on(future)); // 여기서 돈다
}
