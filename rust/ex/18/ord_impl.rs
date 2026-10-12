use std::cmp::Ordering;

#[derive(Debug, PartialEq, Eq, PartialOrd, Ord)]
enum Priority {
    Low,
    Mid,
    High,
}

#[derive(Debug, PartialEq, Eq)]
struct Task {
    priority: Priority,
    title: &'static str,
}

impl Ord for Task {
    // 먼저 할 일이 앞 — 우선순위는 높은 쪽부터, 같으면 제목순
    fn cmp(&self, other: &Self) -> Ordering {
        let by_priority = other.priority.cmp(&self.priority);
        by_priority.then_with(|| self.title.cmp(other.title))
    }
}

impl PartialOrd for Task {
    // Ord 가 정한 순서를 그대로 돌려준다
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

fn main() {
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
    println!("{}", tasks[0] < tasks[3]);
    println!("{:?}", tasks.iter().min().map(|x| x.title));
}
