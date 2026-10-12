// 변형을 적은 순서가 곧 작은 것부터의 순서다
#[derive(Debug, PartialEq, Eq, PartialOrd, Ord)]
enum Priority {
    Low,
    Mid,
    High,
}

// 필드를 적은 순서대로 견준다 — 우선순위 먼저, 같으면 제목
#[derive(Debug, PartialEq, Eq, PartialOrd, Ord)]
struct Task {
    priority: Priority,
    title: &'static str,
}

fn main() {
    println!("{}", Priority::Low < Priority::High);
    println!("{:?}", Priority::Mid.cmp(&Priority::High));

    let t = |priority, title| Task { priority, title };
    let mut tasks = vec![
        t(Priority::Mid, "메일 답장"),
        t(Priority::High, "배포"),
        t(Priority::Low, "책상 정리"),
        t(Priority::High, "장애 보고"),
    ];
    tasks.sort();
    for x in &tasks {
        println!("{:?} {}", x.priority, x.title);
    }
    println!("{:?}", tasks.iter().max());
}
