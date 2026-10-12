use std::cell::RefCell;
use std::collections::{BTreeMap, VecDeque};
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
            // 열쇠는 이 문에서 사라진다. poll 안의 wake 가 다시 잠근다.
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

// ticks 틱을 자고 일어난다. 줄마다 그때의 틱을 찍는다.
async fn nap(timer: Timer, name: &'static str, ticks: u64) {
    println!("틱 {} · {name}: {ticks}틱 잔다", timer.now());
    timer.sleep(ticks).await;
    println!("틱 {} · {name}: 일어났다", timer.now());
}

// 자지 않고 차례만 두 번 양보한다.
async fn busy(timer: Timer, name: &'static str) {
    for step in 1..=2 {
        println!("틱 {} · {name}: 양보 {step}", timer.now());
        Countdown(1).await;
    }
    println!("틱 {} · {name}: 끝", timer.now());
}

fn main() {
    let mut ex = Executor::default();
    let timer = ex.timer.clone();
    ex.spawn(nap(timer.clone(), "가", 3));
    ex.spawn(nap(timer.clone(), "나", 1));
    ex.spawn(busy(timer.clone(), "다"));
    ex.spawn(nap(timer.clone(), "라", 3));
    let left = ex.run();
    println!("poll 순서 {:?}", ex.log);
    println!("끝나지 않은 태스크 {left}, 마지막 틱 {}", timer.now());
}
