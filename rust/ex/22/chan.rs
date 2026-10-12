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

fn main() {
    let (tx, rx) = channel::<u32>();
    let tx2 = tx.clone();
    let mut ex = Executor::default();
    // 0번: 받는 쪽.
    ex.spawn(async move {
        while let Some(value) = rx.recv().await {
            println!("0번: 받았다 {value}");
        }
        println!("0번: 보내는 쪽이 모두 사라졌다");
    });
    // 1번: 1 을 보내고, 차례를 한 번 양보한 뒤에 2 를 보낸다.
    ex.spawn(async move {
        tx.send(1);
        Countdown(1).await;
        tx.send(2);
    });
    // 2번: 10 을 보내고, 차례를 두 번 양보한 뒤에 끝난다.
    ex.spawn(async move {
        tx2.send(10);
        Countdown(2).await;
    });
    let left = ex.run();
    println!("poll 순서 {:?}, 끝나지 않은 태스크 {left}", ex.log);
}
