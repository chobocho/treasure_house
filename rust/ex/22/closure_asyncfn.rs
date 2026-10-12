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

// 받은 것을 같은 인자로 두 번 불러, 두 값을 더한다.
async fn apply(f: impl AsyncFn(u32) -> u32, n: u32) -> u32 {
    f(n).await + f(n).await
}

// mut 로 받아 두 번 부르고, 둘째 값을 낸다.
async fn call_twice(mut f: impl AsyncFnMut(u32) -> usize) -> usize {
    f(10).await;
    f(20).await
}

// 받은 것을 한 번 부른다.
async fn finish(f: impl AsyncFnOnce() -> String) -> String {
    f().await
}

async fn double(n: u32) -> u32 {
    Countdown(1).await;
    n * 2
}

fn main() {
    let base = 100;
    println!("{}", block_on(apply(async |n| base + n, 1)));
    // async fn 도 받는다.
    println!("{}", block_on(apply(double, 4)));

    let mut seen: Vec<u32> = Vec::new();
    let record = async |n| {
        Countdown(1).await;
        seen.push(n);
        seen.len()
    };
    println!("{}", block_on(call_twice(record)));
    println!("{seen:?}");

    let name = String::from("ferris");
    println!("{}", block_on(finish(async move || name)));
}
