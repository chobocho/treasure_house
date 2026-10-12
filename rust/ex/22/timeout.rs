use std::cell::RefCell;
use std::collections::{BTreeMap, VecDeque};
use std::pin::Pin;
use std::rc::Rc;
use std::sync::{Arc, Mutex};
use std::task::{Context, Poll, Wake, Waker};

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
    timer: Timer,
}

impl Executor {
    // 퓨처를 태스크로 만든다. 번호는 tasks 의 칸 번호다.
    // 처음 한 번은 깨운 것으로 쳐서 큐에 넣는다.
    fn spawn(&mut self, future: impl Future<Output = ()> + 'static) {
        let id = self.tasks.len();
        self.tasks.push(Some(Box::pin(future)));
        self.ready.lock().unwrap().push_back(id);
    }

    // 큐가 비고 잠든 태스크도 없을 때까지 돈다.
    // 끝나지 않은 태스크의 수를 돌려준다.
    fn run(&mut self) -> usize {
        loop {
            // 열쇠는 이 let 문까지다. poll 안의 wake 가 다시 잠근다.
            let next = self.ready.lock().unwrap().pop_front();
            let Some(id) = next else {
                // 큐가 비었다. 잠든 태스크가 있으면 틱을 돌려 깨운다.
                if self.timer.advance() {
                    continue;
                }
                break;
            };
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

// 틱으로 세는 시간: 지금의 틱과, 깨울 틱마다 맡아 둔 Waker.
// 키는 (깨울 틱, Sleep 을 만든 순서) 다.
#[derive(Default)]
struct TimerState {
    now: u64,
    made: u64,
    sleepers: BTreeMap<(u64, u64), Waker>,
}

// 실행기와 태스크가 함께 가진다. 복제본은 같은 TimerState 를 본다.
#[derive(Clone, Default)]
struct Timer(Rc<RefCell<TimerState>>);

impl Timer {
    fn now(&self) -> u64 {
        self.0.borrow().now
    }

    // 지금부터 ticks 틱 뒤에 끝나는 퓨처.
    fn sleep(&self, ticks: u64) -> Sleep {
        let mut state = self.0.borrow_mut();
        state.made += 1;
        Sleep {
            timer: self.clone(),
            key: (state.now + ticks, state.made),
        }
    }

    // 가장 이른 깨울 틱으로 건너뛰고, 그 틱의 Waker 를 모두 깨운다.
    // 맡아 둔 Waker 가 없으면 false.
    fn advance(&self) -> bool {
        let mut state = self.0.borrow_mut();
        let Some((&(at, _), _)) = state.sleepers.first_key_value()
        else {
            return false;
        };
        state.now = at;
        while let Some(entry) = state.sleepers.first_entry()
            && entry.key().0 == at
        {
            entry.remove().wake();
        }
        true
    }
}

// 정해 둔 틱이 되면 끝나는 퓨처.
struct Sleep {
    timer: Timer,
    key: (u64, u64),
}

impl Future for Sleep {
    type Output = ();

    fn poll(self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<()> {
        let mut state = self.timer.0.borrow_mut();
        if state.now >= self.key.0 {
            return Poll::Ready(());
        }
        // 아직이다. 그 틱에 깨워 달라고 Waker 를 맡긴다.
        // 다시 물으면 같은 키의 Waker 를 바꿔 넣는다.
        state.sleepers.insert(self.key, cx.waker().clone());
        Poll::Pending
    }
}

impl Drop for Sleep {
    // 버려질 때, 맡겨 둔 Waker 가 남아 있으면 치운다.
    fn drop(&mut self) {
        self.timer.0.borrow_mut().sleepers.remove(&self.key);
    }
}

// 채널의 속: 값이 서는 큐, 살아 있는 보내는 쪽의 수,
// 받는 쪽이 맡긴 Waker.
struct Chan<T> {
    queue: VecDeque<T>,
    senders: usize,
    waiting: Option<Waker>,
}

struct Sender<T>(Rc<RefCell<Chan<T>>>);
struct Receiver<T>(Rc<RefCell<Chan<T>>>);

fn channel<T>() -> (Sender<T>, Receiver<T>) {
    let chan = Rc::new(RefCell::new(Chan {
        queue: VecDeque::new(),
        senders: 1,
        waiting: None,
    }));
    (Sender(chan.clone()), Receiver(chan))
}

impl<T> Sender<T> {
    // 값을 큐에 넣고, 기다리는 받는 쪽이 있으면 깨운다.
    fn send(&self, value: T) {
        let mut chan = self.0.borrow_mut();
        chan.queue.push_back(value);
        if let Some(waker) = chan.waiting.take() {
            waker.wake();
        }
    }
}

impl<T> Clone for Sender<T> {
    fn clone(&self) -> Self {
        self.0.borrow_mut().senders += 1;
        Sender(self.0.clone())
    }
}

impl<T> Drop for Sender<T> {
    // 마지막 보내는 쪽이 사라지면, 기다리는 받는 쪽을 깨워 알린다.
    fn drop(&mut self) {
        let mut chan = self.0.borrow_mut();
        chan.senders -= 1;
        if chan.senders == 0
            && let Some(waker) = chan.waiting.take()
        {
            waker.wake();
        }
    }
}

// recv 가 돌려주는 퓨처.
struct Recv<'a, T>(&'a Receiver<T>);

impl<T> Receiver<T> {
    fn recv(&self) -> Recv<'_, T> {
        Recv(self)
    }
}

impl<T> Future for Recv<'_, T> {
    type Output = Option<T>;

    fn poll(
        self: Pin<&mut Self>,
        cx: &mut Context<'_>,
    ) -> Poll<Option<T>> {
        let mut chan = self.0.0.borrow_mut();
        if let Some(value) = chan.queue.pop_front() {
            return Poll::Ready(Some(value));
        }
        if chan.senders == 0 {
            return Poll::Ready(None);
        }
        // 큐가 비었고 보내는 쪽이 남아 있다. Waker 를 맡기고 기다린다.
        chan.waiting = Some(cx.waker().clone());
        Poll::Pending
    }
}

// 두 퓨처를 함께 묻고, 먼저 Ready 를 낸 쪽의 값을 낸다.
struct Select2<A, B> {
    a: Pin<Box<A>>,
    b: Pin<Box<B>>,
}

fn select2<A, B>(a: A, b: B) -> Select2<A, B> {
    Select2 {
        a: Box::pin(a),
        b: Box::pin(b),
    }
}

impl<A, B> Future for Select2<A, B>
where
    A: Future,
    B: Future<Output = A::Output>,
{
    type Output = A::Output;

    fn poll(
        mut self: Pin<&mut Self>,
        cx: &mut Context<'_>,
    ) -> Poll<Self::Output> {
        // a 를 먼저 묻는다. a 가 끝났으면 b 는 묻지 않는다.
        if let Poll::Ready(value) = self.a.as_mut().poll(cx) {
            return Poll::Ready(value);
        }
        self.b.as_mut().poll(cx)
    }
}

// 값을 기다리되, limit 틱 안에 오지 않으면 그만둔다.
async fn recv_within(
    rx: &Receiver<u32>,
    timer: &Timer,
    limit: u64,
) -> Result<Option<u32>, &'static str> {
    let value = async { Ok(rx.recv().await) };
    let alarm = async {
        timer.sleep(limit).await;
        Err("시간 초과")
    };
    select2(value, alarm).await
}

// 1번은 1 을 보내고, gap 틱을 잔 뒤에 2 를 보낸다.
// 0번은 값마다 3틱까지만 기다린다.
fn demo(gap: u64) {
    let mut ex = Executor::default();
    let timer = ex.timer.clone();
    let (tx, rx) = channel::<u32>();
    let t0 = timer.clone();
    ex.spawn(async move {
        loop {
            let got = recv_within(&rx, &t0, 3).await;
            let now = t0.now();
            match got {
                Ok(Some(value)) => {
                    println!("틱 {now} · 받았다 {value}")
                }
                Ok(None) => {
                    println!("틱 {now} · 보내는 쪽이 사라졌다");
                    break;
                }
                Err(why) => {
                    println!("틱 {now} · {why}");
                    break;
                }
            }
        }
    });
    let t1 = timer.clone();
    ex.spawn(async move {
        tx.send(1);
        t1.sleep(gap).await;
        println!("틱 {} · 2 를 보낸다", t1.now());
        tx.send(2);
    });
    let left = ex.run();
    println!("poll 순서 {:?}", ex.log);
    println!("끝나지 않은 태스크 {left}, 마지막 틱 {}", timer.now());
}

fn main() {
    demo(2);
    demo(5);
}
