use std::cell::RefCell;
use std::collections::VecDeque;
use std::pin::Pin;
use std::rc::Rc;
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
        // (깨워 달라고 하는 줄을 뺐다)
        Poll::Pending
    }
}

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

// 태스크: 값을 내지 않는 퓨처를 상자에 담아 고정한 것.
type Task = Pin<Box<dyn Future<Output = ()>>>;

// 태스크를 큐에 세워 두고 차례로 묻는 실행기.
#[derive(Default)]
struct Executor {
    queue: VecDeque<(usize, Task)>,
    spawned: usize,
    log: Vec<usize>,
}

impl Executor {
    // 퓨처를 태스크로 만들어 큐 뒤에 세운다. 번호는 맡긴 순서다.
    fn spawn(&mut self, future: impl Future<Output = ()> + 'static) {
        let id = self.spawned;
        self.spawned += 1;
        self.queue.push_back((id, Box::pin(future)));
    }

    // 큐가 빌 때까지: 앞에서 꺼내 한 번 묻고, 덜 끝났으면 뒤에 세운다.
    fn run(&mut self) {
        let mut cx = Context::from_waker(Waker::noop());
        while let Some((id, mut task)) = self.queue.pop_front() {
            self.log.push(id);
            if task.as_mut().poll(&mut cx).is_pending() {
                self.queue.push_back((id, task));
            }
        }
    }
}

fn main() {
    let gate = Gate::default();
    let waiting = gate.clone();
    let mut ex = Executor::default();
    ex.spawn(async move {
        waiting.await;
        println!("0번: 문이 열렸다");
    });
    ex.spawn(async move {
        Countdown(3).await;
        println!("1번: 문을 연다");
        gate.open();
    });
    ex.run();
    println!("poll 순서 {:?}", ex.log);
    println!("poll {}번", ex.log.len());
}
