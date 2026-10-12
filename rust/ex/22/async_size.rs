use std::pin::Pin;
use std::task::{Context, Poll};

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
    // 배열이 .await 앞에서 스코프를 벗어난다.
    let short = async {
        let len = {
            let data = [1u8; 64];
            data.len()
        };
        Countdown(1).await;
        len
    };
    // 배열을 .await 뒤에도 쓴다.
    let across = async {
        let data = [1u8; 64];
        Countdown(1).await;
        data.len()
    };
    // 배열과, 그 배열의 칸을 가리키는 참조를 .await 뒤에도 쓴다.
    let with_ref = async {
        let data = [1u8; 64];
        let first = &data[0];
        Countdown(1).await;
        usize::from(*first) + data.len()
    };

    let array = size_of::<[u8; 64]>();
    println!("short < 배열: {}", size_of_val(&short) < array);
    println!("across >= 배열: {}", size_of_val(&across) >= array);
    let grown = size_of_val(&with_ref) - size_of_val(&across);
    let one_ref = grown == size_of::<&u8>();
    println!("with_ref - across == 참조 하나: {one_ref}");
}
