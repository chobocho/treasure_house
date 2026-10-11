#[derive(Debug)]
enum Door {
    Open,
    Closed,
    Locked { code: u32 },
}

enum Action {
    Push,
    Lock(u32),
    Unlock(u32),
}

fn step(door: Door, action: Action) -> Door {
    // (지금 상태, 일어난 일) 을 한꺼번에 가른다.
    match (door, action) {
        (Door::Open, Action::Push) => Door::Closed,
        (Door::Closed, Action::Push) => Door::Open,
        (Door::Closed, Action::Lock(code)) => Door::Locked { code },
        (Door::Locked { code }, Action::Unlock(tried))
            if code == tried =>
        {
            Door::Closed
        }
        (door, _) => door, // 그 밖에는 아무 일도 없다
    }
}

fn main() {
    let mut door = Door::Open;
    for action in [
        Action::Push,
        Action::Lock(42),
        Action::Push,
        Action::Unlock(7),
        Action::Unlock(42),
        Action::Push,
    ] {
        door = step(door, action);
        println!("{door:?}");
    }
}
