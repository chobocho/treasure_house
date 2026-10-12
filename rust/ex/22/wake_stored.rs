use std::cell::RefCell;
use std::pin::{Pin, pin};
use std::rc::Rc;
use std::sync::Arc;
use std::sync::atomic::{AtomicUsize, Ordering};
use std::task::{Context, Poll, Wake, Waker};

// 문이 열렸는지와, 기다리는 쪽이 맡긴 Waker.
#[derive(Default)]
struct Shared {
    open: bool,
    waiting: Option<Waker>,
}

// 문이 열릴 때까지 Pending 인 퓨처. 복제본은 같은 Shared 를 본다.
#[derive(Clone, Default)]
struct Gate(Rc<RefCell<Shared>>);

impl Gate {
    fn open(&self) {
        let mut shared = self.0.borrow_mut();
        shared.open = true;
        // 맡아 둔 Waker 가 있으면 꺼내서 깨운다.
        if let Some(waker) = shared.waiting.take() {
            waker.wake();
        }
    }
}

impl Future for Gate {
    type Output = ();

    fn poll(self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<()> {
        let mut shared = self.0.borrow_mut();
        if shared.open {
            return Poll::Ready(());
        }
        // 아직 못 끝낸다. 나중에 깨울 수 있게 Waker 를 복제해 맡긴다.
        shared.waiting = Some(cx.waker().clone());
        Poll::Pending
    }
}

// 깨운 횟수만 세는 Waker 의 속.
struct Counter(AtomicUsize);

impl Wake for Counter {
    fn wake(self: Arc<Self>) {
        self.0.fetch_add(1, Ordering::SeqCst);
    }
}

fn main() {
    let counter = Arc::new(Counter(AtomicUsize::new(0)));
    let waker = Waker::from(counter.clone());
    let mut cx = Context::from_waker(&waker);
    let woken = || counter.0.load(Ordering::SeqCst);

    let gate = Gate::default();
    let mut waiting = pin!(gate.clone());
    let answer = waiting.as_mut().poll(&mut cx);
    println!("poll: {answer:?} — 깨움 {}번", woken());
    gate.open();
    println!("문을 열었다 — 깨움 {}번", woken());
    let answer = waiting.as_mut().poll(&mut cx);
    println!("poll: {answer:?} — 깨움 {}번", woken());

    // 기다리는 쪽이 없을 때 연 문.
    let early = Gate::default();
    early.open();
    println!("먼저 열었다 — 깨움 {}번", woken());
    let mut late = pin!(early.clone());
    let answer = late.as_mut().poll(&mut cx);
    println!("poll: {answer:?} — 깨움 {}번", woken());
}
