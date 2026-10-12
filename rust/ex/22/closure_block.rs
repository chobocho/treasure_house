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

// 16부의 block_on 에 poll 을 부른 횟수를 세는 줄을 더했다.
fn block_on<F: Future>(future: F) -> F::Output {
    let mut future = pin!(future);
    let mut cx = Context::from_waker(Waker::noop());
    let mut polls = 0;
    loop {
        polls += 1;
        if let Poll::Ready(value) = future.as_mut().poll(&mut cx) {
            println!("poll {polls}번");
            return value;
        }
    }
}

fn main() {
    let mut seen: Vec<u32> = Vec::new();

    // 클로저가 async move 블록을 돌려준다.
    let record = |n: u32| async move {
        Countdown(1).await;
        seen.push(n);
        seen.len()
    };

    let first = record(10);
    println!("퓨처를 만들었다");
    println!("{}", block_on(first));
    println!("{}", block_on(record(20)));
    println!("{seen:?}");
}
//@ expect: E0382
