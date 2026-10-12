use std::cell::RefCell;
use std::collections::VecDeque;
use std::pin::Pin;
use std::rc::Rc;
use std::sync::{Arc, Mutex};
use std::task::{Context, Poll, Wake, Waker};

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

// 다시 물을 태스크의 번호가 서는 큐. 실행기와 Waker 들이 함께 가진다.
type ReadyQueue = Arc<Mutex<VecDeque<usize>>>;

// 깨우면 자기 태스크의 번호를 큐에 넣는 Waker 의 속.
struct TaskWaker {
    id: usize,
    ready: ReadyQueue,
}

impl Wake for TaskWaker {
    fn wake(self: Arc<Self>) {
        self.ready.lock().unwrap().push_back(self.id);
    }
}

// 깨운 태스크만 묻는 실행기.
#[derive(Default)]
struct Executor {
    tasks: Vec<Option<Task>>,
    ready: ReadyQueue,
    log: Vec<usize>,
}

impl Executor {
    // 퓨처를 태스크로 만든다. 번호는 tasks 의 칸 번호다.
    // 처음 한 번은 깨운 것으로 쳐서 큐에 넣는다.
    fn spawn(&mut self, future: impl Future<Output = ()> + 'static) {
        let id = self.tasks.len();
        self.tasks.push(Some(Box::pin(future)));
        self.ready.lock().unwrap().push_back(id);
    }

    // 큐가 빌 때까지 돈다. 끝나지 않은 태스크의 수를 돌려준다.
    fn run(&mut self) -> usize {
        loop {
            // 열쇠는 이 let 문까지다. poll 안의 wake 가 다시 잠근다.
            let next = self.ready.lock().unwrap().pop_front();
            let Some(id) = next else { break };
            let Some(task) = self.tasks[id].as_mut() else {
                println!("({id}번은 이미 끝났다)");
                continue;
            };
            let waker = Waker::from(Arc::new(TaskWaker {
                id,
                ready: self.ready.clone(),
            }));
            let mut cx = Context::from_waker(&waker);
            self.log.push(id);
            if task.as_mut().poll(&mut cx).is_ready() {
                self.tasks[id] = None;
            }
        }
        self.tasks.iter().flatten().count()
    }
}

// u32 를 내는 퓨처를 상자에 담아 고정한 것.
type Fut = Pin<Box<dyn Future<Output = u32>>>;

// 두 퓨처를 함께 묻는 퓨처. 먼저 나온 값은 들고 있는다.
struct Join2 {
    a: Fut,
    b: Fut,
    out_a: Option<u32>,
    out_b: Option<u32>,
}

fn join2(
    a: impl Future<Output = u32> + 'static,
    b: impl Future<Output = u32> + 'static,
) -> Join2 {
    Join2 {
        a: Box::pin(a),
        b: Box::pin(b),
        out_a: None,
        out_b: None,
    }
}

impl Future for Join2 {
    type Output = (u32, u32);

    fn poll(
        mut self: Pin<&mut Self>,
        cx: &mut Context<'_>,
    ) -> Poll<Self::Output> {
        // 값이 이미 나온 쪽은 다시 묻지 않는다.
        if self.out_a.is_none()
            && let Poll::Ready(value) = self.a.as_mut().poll(cx)
        {
            self.out_a = Some(value);
        }
        if self.out_b.is_none()
            && let Poll::Ready(value) = self.b.as_mut().poll(cx)
        {
            self.out_b = Some(value);
        }
        match (self.out_a, self.out_b) {
            (Some(a), Some(b)) => Poll::Ready((a, b)),
            _ => Poll::Pending,
        }
    }
}

// n 번 Pending 을 낸 뒤에 n 을 낸다.
async fn after(n: u32) -> u32 {
    Countdown(n).await;
    n
}

// 0번 태스크는 수 둘을 받아 합을 찍고 문을 연다. 1번은 문을 기다린다.
fn demo(
    label: &'static str,
    pair: impl Future<Output = (u32, u32)> + 'static,
) {
    let gate = Gate::default();
    let waiting = gate.clone();
    let mut ex = Executor::default();
    ex.spawn(async move {
        let (a, b) = pair.await;
        println!("{label}: {a} + {b} = {}", a + b);
        gate.open();
    });
    ex.spawn(async move {
        waiting.await;
        println!("1번: 문이 열렸다");
    });
    let left = ex.run();
    println!("poll 순서 {:?}, 끝나지 않은 태스크 {left}", ex.log);
}

fn main() {
    demo("차례로", async { (after(2).await, after(3).await) });
    demo("함께", join2(after(2), after(3)));
}
