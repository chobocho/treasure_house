use std::pin::{Pin, pin};
use std::task::{Context, Poll, Waker};

// Pending 을 n 번 돌려준 뒤에 끝나는 퓨처.
struct Countdown(u32);

impl Future for Countdown {
    type Output = &'static str;

    fn poll(
        mut self: Pin<&mut Self>,
        cx: &mut Context<'_>,
    ) -> Poll<Self::Output> {
        if self.0 == 0 {
            return Poll::Ready("발사");
        }
        self.0 -= 1;
        cx.waker().wake_by_ref();
        Poll::Pending
    }
}

async fn trip() -> u32 {
    println!("  출발");
    Countdown(1).await;
    println!("  중간");
    Countdown(2).await;
    println!("  도착");
    7
}

fn main() {
    let mut future = pin!(trip());
    let mut cx = Context::from_waker(Waker::noop());
    for turn in 1..=4 {
        println!("{turn}번째 poll");
        let answer = future.as_mut().poll(&mut cx);
        println!("  → {answer:?}");
    }
}
