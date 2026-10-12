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

// 14부의 Noisy: 정리될 때 한 줄을 찍는다.
struct Noisy(&'static str);

impl Drop for Noisy {
    fn drop(&mut self) {
        println!("{} 정리", self.0);
    }
}

// Noisy 를 든 채로 한 번 기다린다.
async fn job(name: &'static str) {
    let _guard = Noisy(name);
    println!("{name}: 시작");
    Countdown(1).await;
    println!("{name}: 끝");
}

fn main() {
    let mut cx = Context::from_waker(Waker::noop());

    // 끝까지 묻는다.
    let mut done = Box::pin(job("가"));
    println!("{:?}", done.as_mut().poll(&mut cx));
    println!("{:?}", done.as_mut().poll(&mut cx));

    // 한 번 묻고 버린다.
    let mut cut = Box::pin(job("나"));
    println!("{:?}", cut.as_mut().poll(&mut cx));
    println!("main: 나 를 버린다");
    drop(cut);
    println!("main: 버렸다");

    // 한 번도 묻지 않고 버린다.
    let never = Box::pin(job("다"));
    drop(never);
    println!("main: 다 도 버렸다");
}
