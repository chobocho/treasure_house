use std::pin::{Pin, pin};
use std::task::{Context, Poll, Waker};

// 물으면 곧바로 값을 내는 퓨처.
struct Answer(u32);

impl Future for Answer {
    type Output = u32;

    fn poll(self: Pin<&mut Self>, _cx: &mut Context<'_>) -> Poll<u32> {
        println!("poll 이 불렸다");
        Poll::Ready(self.0)
    }
}

fn main() {
    let mut future = pin!(Answer(42));
    println!("퓨처를 만들었다");
    let mut cx = Context::from_waker(Waker::noop());
    let answer = future.as_mut().poll(&mut cx);
    println!("{answer:?}");
}
