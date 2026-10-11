#[derive(Debug)]
enum State {
    Idle,
    Running { speed: u32 },
    Done,
}

fn main() {
    let states =
        [State::Idle, State::Running { speed: 90 }, State::Done];

    for s in &states {
        // matches! — "이 모양인가" 를 bool 로.
        let active = matches!(s, State::Running { .. });
        let fast = matches!(s, State::Running { speed } if *speed > 60);
        println!("{s:?}: {active} {fast}");
    }
    let finished =
        states.iter().filter(|s| matches!(s, State::Done)).count();
    println!("{finished}");
}
