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

// 14부의 Noisy: 정리될 때 한 줄을 찍는다.
struct Noisy(&'static str);

impl Drop for Noisy {
    fn drop(&mut self) {
        println!("{} 정리", self.0);
    }
}

// 문이 열리기를 기다린다. 기다리는 동안 Noisy 를 들고 있는다.
async fn wait_job(name: &'static str, gate: Gate) {
    let _guard = Noisy(name);
    println!("{name}: 문을 기다린다");
    gate.await;
    println!("{name}: 문이 열렸다");
}

fn main() {
    // 0번과 3번의 문은 저마다 따로이고, 아무도 열지 않는다.
    // soon 은 2번 태스크가 연다.
    let soon = Gate::default();
    let mut ex = Executor::default();
    ex.spawn(wait_job("0번", Gate::default()));
    ex.spawn(wait_job("1번", soon.clone()));
    ex.spawn(async move {
        Countdown(2).await;
        println!("2번: 문을 연다");
        soon.open();
    });
    ex.spawn(wait_job("3번", Gate::default()));
    let left = ex.run();
    println!("poll 순서 {:?}, 끝나지 않은 태스크 {left}", ex.log);

    println!("main: 실행기를 버린다");
    drop(ex);
    println!("main: 버렸다");
}
