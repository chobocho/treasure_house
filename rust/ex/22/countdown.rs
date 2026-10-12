use std::pin::{Pin, pin};
use std::task::{Context, Poll, Waker};

// Pending 을 n 번 돌려준 뒤에 끝나는 퓨처.
struct Countdown(u32);

impl Future for Countdown {
    type Output = &'static str;

    fn poll(
        mut self: Pin<&mut Self>,
        _cx: &mut Context<'_>,
    ) -> Poll<Self::Output> {
        if self.0 == 0 {
            return Poll::Ready("발사");
        }
        self.0 -= 1;
        Poll::Pending
    }
}

fn main() {
    let mut future = pin!(Countdown(3));
    let mut cx = Context::from_waker(Waker::noop());
    for turn in 1..=4 {
        let answer = future.as_mut().poll(&mut cx);
        println!("{turn}번째 poll: {answer:?}");
    }
}
