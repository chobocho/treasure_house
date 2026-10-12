use std::mem;
use std::pin::Pin;
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

fn main() {
    let mut cx = Context::from_waker(Waker::noop());
    let mut first = Countdown(1);
    let mut second = Countdown(5);

    // pin! 없이, 가변 참조를 그 자리에서 Pin 으로 감싼다.
    let mut pinned = Pin::new(&mut first);
    let answer = pinned.as_mut().poll(&mut cx);
    println!("first 를 물었다: {answer:?}");

    // Pin<&mut T> 를 거쳐 값을 맞바꾸고, &mut T 를 도로 꺼낸다.
    mem::swap(&mut *pinned, &mut second);
    let plain: &mut Countdown = pinned.get_mut();
    println!("남은 수: {} {}", plain.0, second.0);

    // 한 번 poll 한 퓨처를 상자로 옮겨서 이어 묻는다.
    let mut moved = Box::new(second);
    let answer = Pin::new(&mut *moved).poll(&mut cx);
    println!("옮긴 뒤에 물었다: {answer:?}");
}
